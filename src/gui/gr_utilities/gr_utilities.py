import time

from constants import HEARTBEAT_TOPIC
import gradio as gr
from services.heartbeat.kafka_consumer import KafkaConsumer
from services.heartbeat.kafka_heartbeat_producer import KafkaHeartbeatProducer


def gr_build_utilities():
    print(f"Creating consumer with {HEARTBEAT_TOPIC} topics")
    consumer = KafkaConsumer([HEARTBEAT_TOPIC], 'monitoring', 'Monitoring')
    producer = KafkaHeartbeatProducer()

    def update_state():
        __state = consumer.is_running()
        return gr.update(variant='stop' if __state else 'primary', value='Stop consumer' if __state else 'Start consumer')

    def start_stop_consumer():
        print(f"start_stop_consumer ask for state of consumer '{consumer.is_running()}'")
        if consumer.is_running():
            consumer.stop()
            time.sleep(1)
        else:
            consumer.start()
        print(f"start_stop_consumer - Consumer state is {consumer.is_running()}")
        gr.Info(f"Consumer state is {consumer.is_running()}")
        return update_state()

    def send_heartbeat(count):
        producer.send_data(count)
        return

    def send_auto_heartbeat(delay):
        print(delay)
        producer.start_auto_mode(delay)

    with gr.Blocks() as block:
        gr.Markdown(value='# Utilities')
        # _get_consumer_button()
        with gr.Row():
            state = consumer.is_running()
            switch_consumer_button = gr.Button(variant='stop' if state else 'primary',
                                               value='Stop consumer' if state else 'Start consumer', size='sm')

            switch_consumer_button.click(start_stop_consumer, outputs=switch_consumer_button)
        with gr.Row():
            sl_hb_count = gr.Slider(minimum=1, maximum=10, label='Message count', step=1)
            gr.Button("Heart Beat").click(send_heartbeat, sl_hb_count)
        with gr.Row():
            sl_hb_delay = gr.Slider(minimum=1, maximum=10, label='Delay in minutes', step=1)
            gr.Button("Auto Heart Beat").click(send_auto_heartbeat, inputs=sl_hb_delay)
        return block
