# coding: utf-8

"""
The entrance of the gradio
"""

import tyro
import gradio as gr
import os.path as osp
from src.utils.helper import load_description
from src.gradio_pipeline import GradioPipeline
from src.config.crop_config import CropConfig
from src.config.argument_config import ArgumentConfig
from src.config.inference_config import InferenceConfig
import spaces
import cv2

# import gdown
# folder_url = f"https://drive.google.com/drive/folders/1UtKgzKjFAOmZkhNK-OYT0caJ_w2XAnib"
# gdown.download_folder(url=folder_url, output="pretrained_weights", quiet=False)

def partial_fields(target_class, kwargs):
    return target_class(**{k: v for k, v in kwargs.items() if hasattr(target_class, k)})

# set tyro theme
tyro.extras.set_accent_color("bright_cyan")
args = tyro.cli(ArgumentConfig)

# specify configs for inference
inference_cfg = partial_fields(InferenceConfig, args.__dict__)  # use attribute of args to initial InferenceConfig
crop_cfg = partial_fields(CropConfig, args.__dict__)  # use attribute of args to initial CropConfig

gradio_pipeline = GradioPipeline(
    inference_cfg=inference_cfg,
    crop_cfg=crop_cfg,
    args=args
)

@spaces.GPU(duration=240)
def gpu_wrapped_execute_video(*args, **kwargs):
    return gradio_pipeline.execute_video(*args, **kwargs)

@spaces.GPU(duration=240)
def gpu_wrapped_execute_image(*args, **kwargs):
    return gradio_pipeline.execute_image(*args, **kwargs)

def is_square_video(video_path):
    video = cv2.VideoCapture(video_path)

    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

    video.release()
    if width != height:
        raise gr.Error("Error: the video does not have a square aspect ratio. We currently only support square videos")

    return gr.update(visible=True)

# assets
title_md = "assets/gradio_title.md"
example_portrait_dir = "assets/examples/source"
example_video_dir = "assets/examples/driving"
data_examples = [
    [osp.join(example_portrait_dir, "s9.jpg"), osp.join(example_video_dir, "d0.mp4"), True, True, True, True],
    [osp.join(example_portrait_dir, "s6.jpg"), osp.join(example_video_dir, "d0.mp4"), True, True, True, True],
    [osp.join(example_portrait_dir, "s10.jpg"), osp.join(example_video_dir, "d0.mp4"), True, True, True, True],
    [osp.join(example_portrait_dir, "s5.jpg"), osp.join(example_video_dir, "d18.mp4"), True, True, True, True],
    [osp.join(example_portrait_dir, "s7.jpg"), osp.join(example_video_dir, "d19.mp4"), True, True, True, True],
]
#################### interface logic ####################

# Define components first
eye_retargeting_slider = gr.Slider(minimum=0, maximum=0.8, step=0.01, label="target eyes-open ratio")
lip_retargeting_slider = gr.Slider(minimum=0, maximum=0.8, step=0.01, label="target lip-open ratio")
retargeting_input_image = gr.Image(type="filepath")
output_image = gr.Image(type="numpy")
output_image_paste_back = gr.Image(type="numpy")
output_video = gr.Video()
output_video_concat = gr.Video()

with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.HTML(load_description(title_md))
    gr.Markdown(load_description("assets/gradio_description_upload.md"))
    with gr.Row():
        with gr.Accordion(open=True, label="Source Portrait"):
            image_input = gr.Image(type="filepath")
            gr.Examples(
                examples=[
                    [osp.join(example_portrait_dir, "s9.jpg")],
                    [osp.join(example_portrait_dir, "s6.jpg")],
                    [osp.join(example_portrait_dir, "s10.jpg")],
                    [osp.join(example_portrait_dir, "s5.jpg")],
                    [osp.join(example_portrait_dir, "s7.jpg")],
                    [osp.join(example_portrait_dir, "s12.jpg")],
                ],
                inputs=[image_input],
                cache_examples=False,
            )
        with gr.Accordion(open=True, label="Driving Video"):
            video_input = gr.Video()
            gr.Examples(
                examples=[
                    [osp.join(example_video_dir, "d0.mp4")],
                    [osp.join(example_video_dir, "d18.mp4")],
                    [osp.join(example_video_dir, "d19.mp4")],
                    [osp.join(example_video_dir, "d14_trim.mp4")],
                    [osp.join(example_video_dir, "d6_trim.mp4")],
                ],
                inputs=[video_input],
                cache_examples=False,
            )
    with gr.Row():
        with gr.Accordion(open=False, label="Animation Instructions and Options"):
            gr.Markdown(load_description("assets/gradio_description_animation.md"))
            with gr.Row():
                flag_relative_input = gr.Checkbox(value=True, label="relative motion")
                flag_do_crop_input = gr.Checkbox(value=True, label="do crop")
                flag_remap_input = gr.Checkbox(value=True, label="paste-back")
    with gr.Row():
        with gr.Column():
            process_button_animation = gr.Button("🚀 Animate", variant="primary")
        with gr.Column():
            process_button_reset = gr.ClearButton([image_input, video_input, output_video, output_video_concat], value="🧹 Clear")
    with gr.Row():
        with gr.Column():
            with gr.Accordion(open=True, label="The animated video in the original image space"):
                output_video.render()
        with gr.Column():
            with gr.Accordion(open=True, label="The animated video"):
                output_video_concat.render()
    with gr.Row():
        # Examples
        gr.Markdown("## You could also choose the examples below by one click ⬇️")
    with gr.Row():
        gr.Examples(
            examples=data_examples,
            fn=gpu_wrapped_execute_video,
            inputs=[
                image_input,
                video_input,
                flag_relative_input,
                flag_do_crop_input,
                flag_remap_input
            ],
            outputs=[output_image, output_image_paste_back],
            examples_per_page=5,
            cache_examples=False,
        )
    gr.Markdown(load_description("assets/gradio_description_retargeting.md"), visible=True)
    with gr.Row(visible=True):
        eye_retargeting_slider.render()
        lip_retargeting_slider.render()
    with gr.Row(visible=True):
        process_button_retargeting = gr.Button("🚗 Retargeting", variant="primary")
        process_button_reset_retargeting = gr.ClearButton(
            [
                eye_retargeting_slider,
                lip_retargeting_slider,
                retargeting_input_image,
                output_image,
                output_image_paste_back
            ],
            value="🧹 Clear"
        )
    with gr.Row(visible=True):
        with gr.Column():
            with gr.Accordion(open=True, label="Retargeting Input"):
                retargeting_input_image.render()
                gr.Examples(
                    examples=[
                        [osp.join(example_portrait_dir, "s9.jpg")],
                        [osp.join(example_portrait_dir, "s6.jpg")],
                        [osp.join(example_portrait_dir, "s10.jpg")],
                        [osp.join(example_portrait_dir, "s5.jpg")],
                        [osp.join(example_portrait_dir, "s7.jpg")],
                        [osp.join(example_portrait_dir, "s12.jpg")],
                    ],
                    inputs=[retargeting_input_image],
                    cache_examples=False,
                )
        with gr.Column():
            with gr.Accordion(open=True, label="Retargeting Result"):
                output_image.render()
        with gr.Column():
            with gr.Accordion(open=True, label="Paste-back Result"):
                output_image_paste_back.render()
    # binding functions for buttons
    process_button_retargeting.click(
        # fn=gradio_pipeline.execute_image,
        fn=gpu_wrapped_execute_image,
        inputs=[eye_retargeting_slider, lip_retargeting_slider, retargeting_input_image, flag_do_crop_input],
        outputs=[output_image, output_image_paste_back],
        show_progress=True
    )
    process_button_animation.click(
        fn=gpu_wrapped_execute_video,
        inputs=[
            image_input,
            video_input,
            flag_relative_input,
            flag_do_crop_input,
            flag_remap_input
        ],
        outputs=[output_video, output_video_concat],
        show_progress=True
    )
    # image_input.change(
    #     fn=gradio_pipeline.prepare_retargeting,
    #     inputs=image_input,
    #     outputs=[eye_retargeting_slider, lip_retargeting_slider, retargeting_input_image]
    # )
    video_input.upload(
        fn=is_square_video,
        inputs=video_input,
        outputs=video_input
    )

demo.launch(
    server_port=args.server_port,
    share=args.share,
    server_name=args.server_name
)
