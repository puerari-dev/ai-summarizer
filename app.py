import streamlit as st
import os
from audio_extractor import download_youtube_audio, extract_audio_from_video
from audio_chunker import partition_audio_equal, partition_audio_by_timestamps
from transcription import transcribe_audio
from summarization import generate_summary
from youtube_processor import get_video_description, extract_timestamps_from_description
from utils import save_markdown, clean_filename, get_audio_duration

# Configurações da página
st.set_page_config(
    page_title="AI Video Summarizer",
    page_icon="🎥",
    layout="wide"
)

# Constantes
SHORT_DURATION_THRESHOLD = 30 * 60  # 30 minutos
SUPPORTED_LANGUAGES = ["Português", "English"]

def initialize_session_state():
    if "language" not in st.session_state:
        st.session_state.language = "Português"
    if "progress" not in st.session_state:
        st.session_state.progress = 0
    if "costs" not in st.session_state:
        st.session_state.costs = {"transcription": 0, "summary": 0}

def get_text(pt, en):
    return pt if st.session_state.language == "Português" else en

def process_short_audio(audio_path: str, output_prefix: str):
    """Processa áudios curtos"""
    with st.status(get_text("Processando arquivo de áudio curto...", "Processing short audio file..."), expanded=True):
        st.session_state.progress = 25
        transcript, transcript_cost = transcribe_audio(audio_path)
        
        st.session_state.progress = 50
        summary, summary_cost = generate_summary(transcript)
        
        st.session_state.progress = 75
        save_markdown(f"{output_prefix}_transcript.md", transcript)
        save_markdown(f"{output_prefix}_summary.md", summary)
        
        st.session_state.costs["transcription"] = transcript_cost
        st.session_state.costs["summary"] = summary_cost
        st.session_state.progress = 100
        
        return transcript, summary

def process_long_audio_equal(audio_path: str, output_prefix: str, num_chunks: int = 4):
    """Processa áudios longos com particionamento igual"""
    with st.status(get_text("Processando arquivo de áudio longo...", "Processing long audio file..."), expanded=True):
        total_transcript_cost = 0.0
        total_summary_cost = 0.0

        st.write(get_text("Particionando áudio...", "Partitioning audio..."))
        chunk_files = partition_audio_equal(audio_path, num_chunks)
        chunk_transcripts = []
        chunk_summaries = []

        progress_per_chunk = 90 / (num_chunks * 2)  # 90% dividido entre transcrição e resumo de cada chunk
        
        for i, chunk in enumerate(chunk_files):
            st.write(f"{get_text('Transcrevendo parte', 'Transcribing chunk')} {i+1}/{num_chunks}...")
            transcript, chunk_trans_cost = transcribe_audio(chunk)
            total_transcript_cost += chunk_trans_cost
            chunk_transcripts.append(transcript)
            save_markdown(f"{output_prefix}_chunk_{i}_transcript.md", transcript)
            st.session_state.progress += progress_per_chunk

            st.write(f"{get_text('Resumindo parte', 'Summarizing chunk')} {i+1}/{num_chunks}...")
            summary, chunk_sum_cost = generate_summary(transcript)
            total_summary_cost += chunk_sum_cost
            chunk_summaries.append(summary)
            save_markdown(f"{output_prefix}_chunk_{i}_summary.md", summary)
            st.session_state.progress += progress_per_chunk

            os.remove(chunk)

        st.write(get_text("Finalizando...", "Finalizing..."))
        merged_transcript = "\n\n".join(chunk_transcripts)
        merged_summary = "\n\n".join(chunk_summaries)
        final_summary, final_sum_cost = generate_summary(merged_summary)
        total_summary_cost += final_sum_cost

        save_markdown(f"{output_prefix}_merged_transcript.md", merged_transcript)
        save_markdown(f"{output_prefix}_merged_summary.md", merged_summary)
        save_markdown(f"{output_prefix}_final_summary.md", final_summary)

        st.session_state.costs["transcription"] = total_transcript_cost
        st.session_state.costs["summary"] = total_summary_cost
        st.session_state.progress = 100

        return merged_transcript, final_summary

def process_long_audio_timestamps(audio_path: str, output_prefix: str, description: str):
    """Processa áudios longos usando timestamps"""
    timestamps = extract_timestamps_from_description(description)
    if not timestamps:
        st.warning(get_text(
            "Nenhum timestamp encontrado na descrição. Usando particionamento igual.",
            "No timestamps found in description. Using equal partitioning."
        ))
        return process_long_audio_equal(audio_path, output_prefix)

    with st.status(get_text(
        "Processando arquivo de áudio longo com timestamps...",
        "Processing long audio file with timestamps..."
    ), expanded=True):
        total_transcript_cost = 0.0
        total_summary_cost = 0.0

        chunk_info = partition_audio_by_timestamps(audio_path, timestamps)
        section_transcripts = []
        section_summaries = []

        progress_per_section = 90 / (len(chunk_info) * 2)

        for i, (chunk_file, label) in enumerate(chunk_info):
            st.write(f"{get_text('Transcrevendo seção', 'Transcribing section')} {label}...")
            transcript, chunk_trans_cost = transcribe_audio(chunk_file)
            total_transcript_cost += chunk_trans_cost
            section_transcripts.append(f"## {label}\n\n{transcript}")
            save_markdown(f"{output_prefix}_{label}_transcript.md", transcript)
            st.session_state.progress += progress_per_section

            st.write(f"{get_text('Resumindo seção', 'Summarizing section')} {label}...")
            summary, chunk_sum_cost = generate_summary(transcript)
            total_summary_cost += chunk_sum_cost
            section_summaries.append(f"## {label}\n\n{summary}")
            save_markdown(f"{output_prefix}_{label}_summary.md", summary)
            st.session_state.progress += progress_per_section

            os.remove(chunk_file)

        st.write(get_text("Finalizando...", "Finalizing..."))
        merged_transcript = "\n\n".join(section_transcripts)
        merged_summary = "\n\n".join(section_summaries)
        final_summary, final_sum_cost = generate_summary(merged_summary)
        total_summary_cost += final_sum_cost

        save_markdown(f"{output_prefix}_merged_transcript.md", merged_transcript)
        save_markdown(f"{output_prefix}_merged_summary.md", merged_summary)
        save_markdown(f"{output_prefix}_final_summary.md", final_summary)

        st.session_state.costs["transcription"] = total_transcript_cost
        st.session_state.costs["summary"] = total_summary_cost
        st.session_state.progress = 100

        return merged_transcript, final_summary

def main():
    initialize_session_state()

    # Seletor de idioma no canto superior direito
    with st.sidebar:
        st.session_state.language = st.selectbox(
            "🌎 Language / Idioma",
            SUPPORTED_LANGUAGES,
            index=SUPPORTED_LANGUAGES.index(st.session_state.language)
        )

    # Título e descrição
    st.title("🎥 AI Video Summarizer")
    st.markdown(get_text(
        "Transcreva e resuma vídeos do YouTube ou arquivos locais usando IA",
        "Transcribe and summarize YouTube videos or local files using AI"
    ))

    # Input do usuário
    input_method = st.radio(
        get_text("Escolha o método de entrada:", "Choose input method:"),
        [get_text("URL do YouTube", "YouTube URL"), 
         get_text("Arquivo Local", "Local File")]
    )

    input_source = None
    if input_method == get_text("URL do YouTube", "YouTube URL"):
        input_source = st.text_input(
            get_text("Cole a URL do YouTube:", "Paste YouTube URL:"),
            placeholder="https://www.youtube.com/watch?v=..."
        )
    else:
        uploaded_file = st.file_uploader(
            get_text("Escolha um arquivo de vídeo:", "Choose a video file:"),
            type=["mp4", "mov", "avi", "mkv"]
        )
        if uploaded_file:
            # Salvar o arquivo temporariamente
            temp_path = os.path.join("temp_media", uploaded_file.name)
            os.makedirs("temp_media", exist_ok=True)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            input_source = temp_path

    # Opções de processamento
    col1, col2 = st.columns(2)
    with col1:
        partition_method = st.radio(
            get_text("Método de particionamento:", "Partitioning method:"),
            [get_text("Automático", "Automatic"),
             get_text("Igual", "Equal"),
             get_text("Timestamps (apenas YouTube)", "Timestamps (YouTube only)")]
        )

    # Botão de processamento
    if st.button(get_text("Processar Vídeo", "Process Video"), disabled=not input_source):
        st.session_state.progress = 0
        st.session_state.costs = {"transcription": 0, "summary": 0}

        # Criar diretórios necessários
        os.makedirs("temp_media", exist_ok=True)
        os.makedirs("transcription_and_summaries", exist_ok=True)
        audio_file = os.path.join("temp_media", "output.mp3")

        try:
            # Download/extração do áudio
            with st.status(get_text("Preparando áudio...", "Preparing audio..."), expanded=True):
                if input_method == get_text("URL do YouTube", "YouTube URL"):
                    success, video_title = download_youtube_audio(input_source, audio_file)
                    if not success:
                        st.error(get_text(
                            "Falha ao baixar áudio do YouTube.",
                            "Failed to download YouTube audio."
                        ))
                        return
                    description = get_video_description(input_source)
                    base_name = clean_filename(video_title)
                else:
                    if not extract_audio_from_video(input_source, audio_file):
                        st.error(get_text(
                            "Falha ao extrair áudio do vídeo.",
                            "Failed to extract audio from video."
                        ))
                        return
                    description = ""
                    base_name = clean_filename(os.path.splitext(os.path.basename(input_source))[0])

            output_prefix = os.path.join("transcription_and_summaries", base_name)
            
            # Verificar duração e processar
            duration = get_audio_duration(audio_file)
            st.write(f"{get_text('Duração do áudio:', 'Audio duration:')} {duration/60:.1f} min")

            if duration <= SHORT_DURATION_THRESHOLD or partition_method == get_text("Automático", "Automatic"):
                transcript, summary = process_short_audio(audio_file, output_prefix)
            else:
                if (partition_method == get_text("Timestamps (apenas YouTube)", "Timestamps (YouTube only)") 
                    and input_method == get_text("URL do YouTube", "YouTube URL")):
                    transcript, summary = process_long_audio_timestamps(audio_file, output_prefix, description)
                else:
                    transcript, summary = process_long_audio_equal(audio_file, output_prefix)

            # Mostrar resultados
            st.success(get_text("Processamento concluído!", "Processing complete!"))
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader(get_text("Transcrição", "Transcription"))
                st.markdown(transcript)
            with col2:
                st.subheader(get_text("Resumo", "Summary"))
                st.markdown(summary)

            # Mostrar custos
            st.subheader(get_text("Custos Estimados", "Estimated Costs"))
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(get_text("Transcrição", "Transcription"), 
                         f"${st.session_state.costs['transcription']:.4f}")
            with col2:
                st.metric(get_text("Resumo", "Summary"),
                         f"${st.session_state.costs['summary']:.4f}")
            with col3:
                total = st.session_state.costs['transcription'] + st.session_state.costs['summary']
                st.metric(get_text("Total", "Total"), f"${total:.4f}")

        finally:
            # Limpar arquivos temporários
            if os.path.exists(audio_file):
                os.remove(audio_file)
            if input_method != get_text("URL do YouTube", "YouTube URL") and input_source:
                if os.path.exists(input_source):
                    os.remove(input_source)

    # Mostrar barra de progresso se estiver processando
    if st.session_state.progress > 0:
        st.progress(st.session_state.progress / 100)

if __name__ == "__main__":
    main()