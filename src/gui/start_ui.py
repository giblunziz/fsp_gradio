import os

import gradio as gr

from src.gui.gr_settings import gr_settings
from src.gui.gr_utilities import gr_utilities


class FspUi():
    __application = None

    def __init__(self):
        self.__application = self.__gr_main()

    def __gr_main(self):
        p_settings = gr_settings.gr_build_settings()
        p_utilities = gr_utilities.gr_build_utilities()

        log_path = os.getenv('LOG_PATH')
        log_file = log_path + 'output.log'

        with gr.Blocks() as block:
            gr.TabbedInterface([p_utilities, p_settings], ["Utilities", "Settings"])

        gr.Warning("Started")
        return block

    def launch(self):
        self.__application.launch()
