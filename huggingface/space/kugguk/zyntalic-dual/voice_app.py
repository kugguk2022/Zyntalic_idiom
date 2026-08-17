"""Repository-only v0.1 voice lab. This file is not used by the HF Space."""

import gradio as gr

from voice_lab import render_self_voice


with gr.Blocks(title="Zyntalic v0.1 Voice Lab") as voice_demo:
    gr.Markdown(
        "# Zyntalic v0.1 Voice Lab\n"
        "Record a clean 6–12 second film take. The local pipeline transcribes it, "
        "creates a deterministic Zyntalic line, and renders that line in the "
        "reference voice. Audio stays on this machine."
    )
    reference = gr.Audio(sources=["microphone", "upload"], type="filepath", label="Your reference performance")
    consent = gr.Checkbox(label="I own this voice or have the speaker's permission for this production")
    render = gr.Button("Create alien-language take", variant="primary")
    with gr.Row():
        transcript = gr.Textbox(label="Detected line")
        surface = gr.Textbox(label="Zyntalic v0.1 line")
    output = gr.Audio(label="Voice-matched Zyntalic take", type="numpy")
    render.click(render_self_voice, [reference, consent], [transcript, surface, output], api_name=False)
    gr.Markdown("Built by the Zyntalic team with Codex as a development teammate.")


if __name__ == "__main__":
    voice_demo.launch(inbrowser=True)
