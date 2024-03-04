import datetime, os

import gradio
import gradio as gr

from gui.gr_utilities import gr_utilities
from gui.gr_settings import gr_settings


if __name__ == '__main__':
    def gr_main():
        p_settings = gr_settings.gr_build_settings()
        p_utilities = gr_utilities.gr_build_utilities()

        log_path = os.getenv('LOG_PATH')
        log_file = log_path + 'output.log'

        def read_logs():
            try:
                with open(log_file, 'r') as f:
                    return f.read()
            except FileNotFoundError:
                return "No log at all in " + log_file + ": " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                raise

        with gr.Blocks() as block:
            gr.TabbedInterface([p_utilities, p_settings], ["Utilities", "Settings"])
            with gr.Blocks() as log_block:
                logs = gr.Textbox(label="Logs", interactive=False, autoscroll=True, show_copy_button=True)
                log_block.load(read_logs, None, logs, every=1)

        gr.Warning("Started")
        return block
    gr_main().launch()
