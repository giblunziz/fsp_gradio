import gradio as gr


def gr_build_settings_topic_selector():
    with gr.Blocks() as block:
        gr.Markdown(value='## Topics')
        with gr.Column():
            selector = gr.Dropdown(
                ["Heart Beat", "Heart Beat Response", "Invoice Request Incoming"], value=[], multiselect=True,
                label="Topics",
                info="Choose wich event you want to monitor.")

    return block

def gr_build_dataset_folder():
    with gr.Blocks() as block:
        gr.Markdown(value='Dataset root folder')
        gr.Textbox("datasets/")
        gr.FileExplorer(glob='datasets/*', scale = 1, file_count = 'single' )
    return block
def gr_build_settings():
    with gr.Blocks() as block:
        gr.Markdown(value='# Settings')
        gr.Button("Apply changes", variant='primary')
        gr_build_settings_topic_selector()
        gr_build_dataset_folder()
    return block
