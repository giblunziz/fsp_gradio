import gradio as gr

state=False
def switch_button():
    global state
    state = not state
    return gr.update(variant = 'stop' if state else 'primary', value= 'Stop' if state else 'Start')

with gr.Blocks() as test:
    button = gr.Button("Start!", variant='primary')
    button.click(switch_button, outputs=button)


test.launch(debug=True)