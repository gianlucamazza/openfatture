"""AI voice chat command."""

import typer

from openfatture.ai.agents.chat_agent import ChatAgent
from openfatture.ai.providers.factory import create_provider
from openfatture.ai.voice import VoiceAssistant, create_voice_provider
from openfatture.cli.lifespan import get_event_bus, run_sync_with_lifespan
from openfatture.core.events.ai_events import AICommandCompletedEvent, AICommandStartedEvent
from openfatture.utils.config import get_settings

from ._app import app, console, logger


@app.command("voice-chat")
def ai_voice_chat(
    duration: int = typer.Option(5, "--duration", "-d", help="Recording duration in seconds"),
    sample_rate: int = typer.Option(16000, "--sample-rate", "-s", help="Audio sample rate (Hz)"),
    channels: int = typer.Option(1, "--channels", "-c", help="Number of audio channels"),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Interactive mode (press Enter to record)"
    ),
    save_audio: bool = typer.Option(False, "--save-audio", help="Save audio files to disk"),
    no_playback: bool = typer.Option(False, "--no-playback", help="Disable audio playback"),
) -> None:
    """
    Interactive voice chat with AI assistant.

    This command enables voice-based interaction with the AI assistant:
    1. Records audio from your microphone
    2. Transcribes speech to text (STT)
    3. Processes with LLM (ChatAgent)
    4. Synthesizes response to speech (TTS)
    5. Plays back the audio response

    Modes:
    - Single recording: Record once for specified duration
    - Interactive: Press Enter to start recording, record for duration, repeat

    Requirements:
    - Microphone access
    - OPENAI_API_KEY in environment (for Whisper STT and TTS)

    Examples:
        openfatture ai voice-chat --duration 5
        openfatture ai voice-chat --interactive --duration 10
        openfatture ai voice-chat -i -d 8 --save-audio
        openfatture ai voice-chat --no-playback  # Text output only
    """
    run_sync_with_lifespan(
        _run_voice_chat(duration, sample_rate, channels, interactive, save_audio, no_playback)
    )


async def _run_voice_chat(
    duration: int,
    sample_rate: int,
    channels: int,
    interactive: bool,
    save_audio: bool,
    no_playback: bool,
) -> None:
    """Run voice chat session with audio recording and playback."""
    import io
    import time
    import wave
    from pathlib import Path

    try:
        import sounddevice as sd
    except ImportError:
        console.print(
            "[bold red]Error:[/bold red] Audio dependencies not installed.\n"
            "Install with: [cyan]uv sync[/cyan]\n"
        )
        raise typer.Exit(1)

    # Get event bus and settings
    event_bus = get_event_bus()
    settings = get_settings()

    # Check if voice is enabled in settings
    if not settings.voice_enabled:
        console.print(
            "[bold yellow]Voice features are not enabled in settings.[/bold yellow]\n"
            "Set OPENFATTURE_VOICE_ENABLED=true in .env\n"
        )

    # Verify API key
    if not settings.openai_api_key:
        console.print(
            "[bold red]Error:[/bold red] OPENAI_API_KEY not set.\n"
            "Voice features require OpenAI API access for Whisper STT and TTS.\n"
        )
        raise typer.Exit(1)

    console.print("[bold blue]Voice Chat Assistant[/bold blue]\n")
    console.print(f"Recording: {duration}s at {sample_rate}Hz, {channels} channel(s)")
    console.print(f"Mode: {'Interactive' if interactive else 'Single recording'}\n")

    # Track execution metrics
    start_time = time.time()
    success = False
    total_interactions = 0

    # Publish AICommandStartedEvent
    if event_bus:
        event_bus.publish(
            AICommandStartedEvent(
                command="voice-chat",
                user_input="Voice chat session",
                provider="openai",
                model="whisper-1 + gpt",
                parameters={
                    "duration": duration,
                    "sample_rate": sample_rate,
                    "interactive": interactive,
                },
            )
        )

    try:
        # Create voice provider and assistant
        with console.status("[bold green]Initializing voice assistant..."):
            voice_provider = create_voice_provider(api_key=settings.openai_api_key)
            chat_provider = create_provider()
            chat_agent = ChatAgent(provider=chat_provider)
            assistant = VoiceAssistant(
                voice_provider=voice_provider,
                chat_agent=chat_agent,
                enable_tts=not no_playback,
            )

        console.print("[green]Voice assistant ready[/green]\n")

        # List available audio devices
        devices = sd.query_devices()
        default_input = sd.default.device[0]
        console.print(f"[dim]Using microphone: {devices[default_input]['name']}[/dim]\n")

        # Interactive or single mode
        if interactive:
            console.print(
                "Press [bold cyan]Enter[/bold cyan] to start recording, or type 'exit' to quit.\n"
            )

        conversation_number = 0

        while True:
            conversation_number += 1

            # Wait for user input in interactive mode
            if interactive:
                user_command = console.input(
                    f"[bold green]Recording {conversation_number}:[/bold green] "
                ).strip()
                if user_command.lower() in ("exit", "quit", "q"):
                    console.print("[dim]Goodbye! [/dim]\n")
                    break

            # Record audio
            console.print(f"[bold yellow]Recording for {duration} seconds...[/bold yellow]")
            try:
                audio_data = sd.rec(
                    int(duration * sample_rate),
                    samplerate=sample_rate,
                    channels=channels,
                    dtype="int16",
                )
                sd.wait()  # Wait for recording to finish
                console.print("[green]Recording complete[/green]\n")
            except Exception as e:
                console.print(f"[bold red]Recording failed:[/bold red] {e}\n")
                if not interactive:
                    raise typer.Exit(1)
                continue

            # Convert to WAV bytes
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(2)  # 16-bit audio
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            wav_bytes = wav_buffer.getvalue()

            # Save audio if requested
            if save_audio:
                timestamp = int(time.time())
                audio_path = Path(f"voice_input_{timestamp}.wav")
                audio_path.write_bytes(wav_bytes)
                console.print(f"[dim]Saved recording: {audio_path}[/dim]\n")

            # Process with voice assistant
            with console.status("[bold green]Processing voice input..."):
                try:
                    save_path = (
                        Path(f"voice_response_{int(time.time())}.mp3") if save_audio else None
                    )
                    response = await assistant.process_voice_input(
                        audio=wav_bytes,
                        save_audio=save_path,
                    )
                except Exception as e:
                    console.print(f"[bold red]Processing failed:[/bold red] {e}\n")
                    if not interactive:
                        raise typer.Exit(1)
                    continue

            # Display transcription
            console.print(f"[cyan]You said:[/cyan] {response.transcription.text}")
            console.print(
                f"[dim](Language: {response.transcription.language}, "
                f"STT: {response.stt_latency_ms:.0f}ms)[/dim]\n"
            )

            # Display LLM response
            console.print(f"[magenta]Assistant:[/magenta] {response.llm_response}")
            console.print(
                f"[dim](LLM: {response.llm_latency_ms:.0f}ms, "
                f"Tokens: {response.llm_metadata['tokens']})[/dim]\n"
            )

            # Play audio response
            if response.synthesis and not no_playback:
                console.print("[bold yellow]Playing response...[/bold yellow]")
                try:
                    # OpenAI TTS returns MP3 by default, we need to decode it
                    # For simplicity, save to temp file and inform user
                    # TODO: Add MP3 decoding for direct playback
                    import tempfile

                    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                        tmp.write(response.synthesis.audio_data)
                        tmp_path = tmp.name

                    console.print(
                        f"[yellow]Audio saved to:[/yellow] {tmp_path}\n"
                        "[dim]Direct playback requires MP3 decoding. "
                        "Use --save-audio to save responses.[/dim]\n"
                    )
                except Exception as e:
                    console.print(f"[yellow]Audio save failed:[/yellow] {e}\n")

            # Save response audio if requested
            if save_audio and response.synthesis:
                response_path = Path(f"voice_response_{int(time.time())}.mp3")
                response_path.write_bytes(response.synthesis.audio_data)
                console.print(f"[dim]Saved response: {response_path}[/dim]\n")

            # Display metrics
            console.print("[dim]─────────────────────────────[/dim]")
            console.print(
                f"[dim]Total latency: {response.total_latency_ms:.0f}ms "
                f"(STT: {response.stt_latency_ms:.0f}ms, "
                f"LLM: {response.llm_latency_ms:.0f}ms, "
                f"TTS: {response.tts_latency_ms or 0:.0f}ms)[/dim]"
            )
            if response.llm_metadata.get("cost_usd"):
                console.print(f"[dim]Cost: ${response.llm_metadata['cost_usd']:.4f}[/dim]")
            console.print("[dim]─────────────────────────────[/dim]\n")

            total_interactions += 1

            # Exit if not interactive
            if not interactive:
                break

        # Mark as successful
        success = True

    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted by user[/dim]")
        success = False
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}\n")
        logger.error("voice_chat_error", error=str(e), error_type=type(e).__name__)
        raise typer.Exit(1)
    finally:
        # Publish AICommandCompletedEvent
        if event_bus:
            latency_ms = (time.time() - start_time) * 1000
            event_bus.publish(
                AICommandCompletedEvent(
                    command="voice-chat",
                    success=success,
                    tokens_used=0,  # Voice sessions aggregate multiple interactions
                    cost_usd=0.0,
                    latency_ms=latency_ms,
                )
            )
