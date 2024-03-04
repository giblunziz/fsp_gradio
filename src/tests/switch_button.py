import gradio as gr

state = False


def switch_button():
    global state
    state = not state
    return gr.update(variant='stop' if state else 'primary', value='Stop' if state else 'Start')


with gr.Blocks() as test:

    def open_group():
        raise gr.Error("Oops")
        return gr.update(open=True, visible=True)

    button = gr.Button("Start!", variant='primary')
    button.click(switch_button, outputs=button)
    with gr.Row():
        b1 = gr.Button("Open group 1")
        b2 = gr.Button("Open group 2")
    with gr.Group():
        with gr.Accordion("# Group #1", open=False, visible=False) as gr1:
            gr.Markdown("# Group #1")
        with gr.Accordion("Group #2", open=False, visible=False) as gr2:
            gr.Markdown("# Group #2")
    b1.click(open_group, outputs=gr1)
    b2.click(open_group, outputs=gr2)


test.launch(debug=True)
