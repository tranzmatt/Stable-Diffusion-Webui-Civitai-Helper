""" -*- coding: UTF-8 -*-
Sections for civitai_helper tab.
"""

import gradio as gr
from scripts.ch_lib import model
from scripts.ch_lib import js_action_civitai
from scripts.ch_lib import model_action_civitai
from scripts.ch_lib import civitai
from scripts.ch_lib import duplicate_check
from scripts.ch_lib import util

model_types = list(model.folders.keys())

def scan_models_section():
    """ Scan Models Section """
    with gr.Row():
        gr.Markdown("### Scan Models for Civitai")
    with gr.Row():
        with gr.Column():
            scan_model_types_drop = gr.CheckboxGroup(
                choices=model_types,
                label="Model Types",
                value=model_types
            )
            nsfw_preview_scan_drop = gr.Dropdown(
                label="Block NSFW Level Above",
                choices=civitai.NSFW_LEVELS[1:],
                value=util.get_opts("ch_nsfw_preview_threshold"),
                elem_id="ch_nsfw_preview_scan_drop"
            )
    with gr.Row():
        with gr.Column():
            refetch_old_ckb = gr.Checkbox(
                label="Replace Old Metadata Formats*",
                value=False,
                elem_id="ch_refetch_old_ckb"
            )
            gr.HTML("""
                * [<a href=https://github.com/zixaphir/Stable-Diffusion-Webui-Civitai-Helper/wiki/Metadata-Format-Changes>wiki</a>] Do not use this option if you have made changes with the metadata editor without backing up your data!!<br><br>
                """)

        with gr.Column():
            scan_model_civitai_btn = gr.Button(
                value="Scan",
                variant="primary",
                elem_id="ch_scan_model_civitai_btn"
            )

            scan_civitai_info_image_meta_btn = gr.Button(
                value="Update image generation information (Experimental)",
                variant="primary",
                elem_id="ch_Scan_civitai_info_image_meta_btn"
            )

    with gr.Row():
        scan_model_log_md = gr.Markdown(
            value="Scanning takes time, just wait. Check console log for details",
            elem_id="ch_scan_model_log_md"
        )

    # ====events====
    scan_model_civitai_btn.click(
        model_action_civitai.scan_model,
        inputs=[
            scan_model_types_drop,
            nsfw_preview_scan_drop, refetch_old_ckb
        ],
        outputs=scan_model_log_md
    )

    scan_civitai_info_image_meta_btn.click(
        model.scan_civitai_info_image_meta,
        outputs=scan_model_log_md
    )

def get_model_info_by_url_section():
    """ Get Civitai Model Info by Model Page URL Section """

    def get_model_names_by_input(model_type, empty_info_only):
        names = civitai.get_model_names_by_input(model_type, empty_info_only)
        return model_name_drop.update(choices=names)

    no_info_model_names = civitai.get_model_names_by_input("ckp", False)

    with gr.Column():
        gr.Markdown("### Get Model Info from Civitai by URL")
        gr.Markdown("Use this when scanning can not find a local model on civitai")
        with gr.Row():
            with gr.Column(scale=2):
                model_type_drop = gr.Dropdown(
                    choices=model_types,
                    label="Model Type",
                    value="ckp",
                    multiselect=False,
                    elem_classes="ch_vpadding"
                )
            with gr.Column(scale=1):
                empty_info_only_ckb = gr.Checkbox(
                    label="Only Show Models have no Info",
                    value=False,
                    elem_id="ch_empty_info_only_ckb",
                    elem_classes="ch_vpadding"
                )
        with gr.Row():
            with gr.Column(scale=2):
                model_name_drop = gr.Dropdown(
                    choices=no_info_model_names,
                    label="Model",
                    value="",
                    multiselect=False
                )
            with gr.Column(scale=1):
                nsfw_preview_url_drop = gr.Dropdown(
                    label="Block NSFW Level Above",
                    choices=civitai.NSFW_LEVELS[1:],
                    value=util.get_opts("ch_nsfw_preview_threshold"),
                    elem_id="ch_nsfw_preview_url_drop"
                )
        with gr.Row():
            with gr.Column(scale=2, elem_classes="justify-bottom"):
                model_url_or_id_txtbox = gr.Textbox(
                    label="Civitai URL",
                    lines=1,
                    value=""
                )
            with gr.Column(scale=1, elem_classes="justify-bottom"):
                get_civitai_model_info_by_id_btn = gr.Button(
                    value="Get Model Info from Civitai",
                    variant="primary"
                )

    get_model_by_id_log_md = gr.Markdown("")

    # ====events====
    model_type_drop.change(
        get_model_names_by_input,
        inputs=[
            model_type_drop, empty_info_only_ckb
        ],
        outputs=model_name_drop
    )
    empty_info_only_ckb.change(
        get_model_names_by_input,
        inputs=[
            model_type_drop, empty_info_only_ckb
        ],
        outputs=model_name_drop
    )

    get_civitai_model_info_by_id_btn.click(
        model_action_civitai.get_model_info_by_input,
        inputs=[
            model_type_drop, model_name_drop,
            model_url_or_id_txtbox, nsfw_preview_url_drop
        ],
        outputs=get_model_by_id_log_md
    )

def download_section():
    """ Download Models Section """

    model_filetypes = civitai.FILE_TYPES
    file_elems = {}

    dl_state = gr.State({
        "model_info": {},
        "filenames": {
            # dl_version_str: filename,
        },
        "previews": {
            # dl_version_str: [{url: url, nsfw: nsfw}],
        },
        "files": {
            # dl_version_str: {
            #   Model: bool,
            #   Config: bool,
            #   ...
            # }
        },
        "files_count": {
            # dl_version_str: int
        },
        "filtered_previews": []
    })

    def get_model_info_by_url(url, subfolder, state):
        data = model_action_civitai.get_model_info_by_url(url)

        if not data:
            return None

        state = {
            "model_info": {},
            "filenames": {},
            "previews": {},
            "files": {},
            "files_count": {},
            "filtered_previews": []
        }

        subfolders = sorted(data["subfolders"])
        version_strs = data["version_strs"]
        filenames = data["filenames"]

        if subfolder == "" or subfolder not in subfolders:
            subfolder = "/"

        state["model_info"] = data["model_info"]
        state["previews"] = data["previews"]

        for filename, version in zip(filenames, version_strs):
            state["filenames"][version] = filename

        for version_files, version in zip(data["files"], version_strs):
            filetypes = state["files"][version] = {}
            files_count = 0
            unhandled_files = []
            for filedata in version_files:
                files_count += 1
                ch_filedata = {
                    "id": filedata["id"],
                    "name": filedata["name"],
                }

                if filedata["type"] in model_filetypes:
                    filetypes[filedata["type"]] = (True, ch_filedata)
                    continue

                unhandled_files.append(f"{ch_filedata['id']}: {ch_filedata['name']}")

            if len(unhandled_files) > 0:
                filetypes["unhandled_files"] = "\n".join(unhandled_files)
            else:
                filetypes["unhandled_files"] = None

            state["files_count"][version] = files_count

        return [
            state, data["model_name"], data["model_type"],
            dl_subfolder_drop.update(
                choices=subfolders,
                value=subfolder
            ),
            dl_version_drop.update(
                choices=version_strs,
                value=version_strs[0]
            ),
            files_row.update(
                visible=True
            )
        ]

    def filter_previews(previews, nsfw_preview_url_drop):
        images = []
        for preview in previews:
            if civitai.should_skip(nsfw_preview_url_drop, preview["nsfw"]):
                continue
            if preview["type"] == "image":
                # Civitai added videos as previews, and webui does not like it
                images.append(preview["url"])

        return images

    def update_dl_inputs(state, dl_version, nsfw_threshold, dl_preview_index):
        filename = state["filenames"][dl_version]

        if not filename:
            filename = dl_filename_txtbox.value

        file_parts = filename.split(".")
        ext = file_parts.pop()
        base = ".".join(file_parts)

        previews = filter_previews(state["previews"][dl_version], nsfw_threshold)
        state["filtered_previews"] = previews

        preview = None
        if len(previews) > dl_preview_index:
            preview = previews[dl_preview_index]
        elif len(previews) > 0:
            preview = previews[0]

        output_add = []

        for key, elems in file_elems.items():
            filedata = state["files"][dl_version].get(key, False)

            visible = False
            filename = ""
            if filedata:
                _, data = filedata
                visible = True
                filename = data["name"]

            output_add.append(elems["txtbx"].update(value=filename))
            output_add.append(elems["row"].update(visible=visible))

        return [
            state,
            dl_filename_txtbox.update(
                value=base
            ),
            dl_extension_txtbox.update(
                value=ext
            ),
            dl_preview_img.update(
                value=previews
            ),
            dl_preview_url.update(
                value=preview
            ),
            download_all_row.update(
                visible=(state["files_count"][dl_version] > 1)
            )
        ] + output_add

    def update_dl_files_visibility(dl_all):
        files_chkboxes = []
        for chkbox in ch_dl_model_types_visibility:
            files_chkboxes.append(
                chkbox.update(
                    visible=not dl_all
                )
            )

        return files_chkboxes

    def update_dl_preview_url(state, dl_preview_index):
        preview_url = state["filtered_previews"][dl_preview_index]

        return dl_preview_url.update(
            value=preview_url
        )

    def update_dl_preview_index(evt: gr.SelectData):
        # For some reason, you can't pass gr.SelectData and
        # inputs at the same time. :/

        return dl_preview_index.update(
            value=evt.index
        )

    with gr.Row():
        gr.Markdown("### Download Model")

    with gr.Row():
        with gr.Column(scale=2, elem_id="ch_dl_model_inputs"):

            gr.Markdown(value="**1. Add URL and retrieve Model Info**")

            with gr.Row():
                with gr.Column(scale=2, elem_classes="justify-bottom"):
                    dl_model_url_or_id_txtbox = gr.Textbox(
                        label="Civitai URL",
                        lines=1,
                        max_lines=1,
                        value="",
                        placeholder="Model URL or Model ID"
                    )
                with gr.Column(elem_classes="justify-bottom"):
                    dl_model_info_btn = gr.Button(
                        value="Get Model Info by Civitai Url",
                        variant="primary"
                    )

            gr.Markdown(value="**2. Pick Subfolder and Model Version**")

            with gr.Row(elem_classes="ch_grid"):
                dl_model_name_txtbox = gr.Textbox(
                    label="Model Name",
                    interactive=False,
                    lines=1,
                    max_lines=1,
                    min_width=320,
                    value=""
                )
                dl_model_type_txtbox = gr.Textbox(
                    label="Model Type",
                    interactive=False,
                    lines=1,
                    max_lines=1,
                    min_width=320,
                    value=""
                )
                dl_version_drop = gr.Dropdown(
                    choices=[],
                    label="Model Version",
                    value="",
                    min_width=320,
                    multiselect=False
                )
                dl_subfolder_drop = gr.Dropdown(
                    choices=[],
                    label="Sub-folder",
                    value="",
                    min_width=320,
                    multiselect=False
                )
                dl_duplicate_drop = gr.Dropdown(
                    choices=["Skip", "Overwrite", "Rename New"],
                    label="Duplicate File Behavior",
                    value="Skip",
                    min_width=320,
                    multiselect=False
                )
                nsfw_preview_dl_drop = gr.Dropdown(
                    label="Block NSFW Level Above",
                    choices=civitai.NSFW_LEVELS[1:],
                    value=util.get_opts("ch_nsfw_preview_threshold"),
                    min_width=320,
                    elem_id="ch_nsfw_preview_dl_drop"
                )

            with gr.Column(
                visible=False,
                variant="panel"
            ) as files_row:

                with gr.Row(variant="compact"):
                    gr.Markdown("**Files**")

                ch_output_add = []
                ch_dl_model_types = []
                ch_dl_model_types_visibility = []

                for filetype in model_filetypes:
                    with gr.Row(
                        visible=False,
                        equal_height=True,
                    ) as row:
                        file_elems[filetype] = elems = {}
                        elems["row"] = row

                        with gr.Column(scale=0, min_width=24, elem_classes="flex-center") as ckb_column:
                            elems["ckb"] = filetype_ckb = gr.Checkbox(
                                label="",
                                value=True,
                                min_width=0,
                                interactive=(not filetype == "Model")
                            )
                        with gr.Column(scale=1, min_width=0):
                            elems["txtbx"] = gr.Textbox(
                                value="",
                                interactive=False,
                                label=filetype,
                                max_lines=1,
                                min_width=0
                            )

                        ch_dl_model_types_visibility.append(ckb_column)
                        ch_dl_model_types.append(filetype_ckb)

                        ch_output_add.append(elems["txtbx"])
                        ch_output_add.append(row)

                with gr.Row(visible=False) as unhandled_files_row:
                    file_elems["unhandled_files"] = elems = {}
                    elems["row"] = row

                    elems["txtbx"] = gr.Textbox(
                        value="",
                        interactive=False,
                        label="Unhandled Files (Files that we don't know what to do with but will still downloaded with \"Download All Files\")",
                    )

                    ch_output_add.append(elems["txtbx"])
                    ch_output_add.append(unhandled_files_row)

                with gr.Row(visible=False) as download_all_row:
                    dl_all_ckb = gr.Checkbox(
                        label="Download All Files",
                        value=False,
                        elem_id="ch_dl_all_ckb",
                        elem_classes="ch_vpadding"
                    )

        with gr.Column(scale=1, elem_id="ch_preview_col", min_width=512):
            with gr.Row(elem_classes="flex-center"):
                dl_preview_img = gr.Gallery(
                    show_label=True,
                    label="Preview Image",
                    value=None,
                    elem_id="ch_dl_preview_img",
                    allow_preview=True,
                    preview=False,
                    object_fit="scale-down"
                )
                dl_preview_url = gr.Textbox(
                    value="",
                    visible=False,
                    elem_id="ch_dl_preview_url"
                )
                dl_preview_index = gr.Number(
                    value=0,
                    visible=False,
                    elem_id="ch_dl_preview_index",
                    precision=0
                )

    with gr.Row():
        with gr.Column(scale=2, elem_classes="justify-bottom"):
            dl_filename_txtbox = gr.Textbox(
                label="Rename Model",
                value="",
                lines=1,
                max_lines=1,
                elem_id="ch_dl_filename_txtbox",
                elem_classes="ch_vpadding"
            )
            dl_extension_txtbox = gr.Textbox(
                label="Model extension",
                value="",
                elem_id="ch_dl_extension_txtbox",
                visible=False
            )

        with gr.Column(elem_classes="justify-bottom"):
            dl_civitai_model_by_id_btn = gr.Button(
                value="3. Download Model",
                elem_classes="ch_vmargin",
                variant="primary"
            )

    with gr.Row():
        dl_log_md = gr.Markdown(
            value="Check Console log for Downloading Status"
        )

    # ====events====
    dl_model_info_btn.click(
        get_model_info_by_url,
        inputs=[
            dl_model_url_or_id_txtbox, dl_subfolder_drop, dl_state
        ],
        outputs=[
            dl_state, dl_model_name_txtbox,
            dl_model_type_txtbox, dl_subfolder_drop,
            dl_version_drop, files_row
        ]
    )

    dl_inputs = [
            dl_state, dl_model_type_txtbox,
            dl_subfolder_drop, dl_version_drop,
            dl_filename_txtbox, dl_extension_txtbox,
            dl_all_ckb, nsfw_preview_dl_drop,
            dl_duplicate_drop, dl_preview_url
        ] + ch_dl_model_types

    dl_civitai_model_by_id_btn.click(
        model_action_civitai.dl_model_by_input,
        inputs=dl_inputs,
        outputs=dl_log_md
    )

    ver_outputs = [
        dl_state, dl_filename_txtbox, dl_extension_txtbox,
        dl_preview_img, dl_preview_url, download_all_row,
    ] + ch_output_add

    dl_version_drop.change(
        update_dl_inputs,
        inputs=[dl_state, dl_version_drop, nsfw_preview_dl_drop, dl_preview_index],
        outputs=ver_outputs
    )
    dl_all_ckb.change(
        update_dl_files_visibility,
        inputs=dl_all_ckb,
        outputs=ch_dl_model_types_visibility
    )
    nsfw_preview_dl_drop.change(
        update_dl_inputs,
        inputs=[dl_version_drop, dl_state, nsfw_preview_dl_drop],
        outputs=ver_outputs
    )
    # Gradio has so many issues with Gradio.Gallery...
    dl_preview_img.select(
        update_dl_preview_index,
        None,
        dl_preview_index
    )
    dl_preview_index.change(
        update_dl_preview_url,
        [dl_state, dl_preview_index],
        dl_preview_url
    )


def scan_for_duplicates_section():
    """ Scan Duplicate Models Section """
    with gr.Column():
        gr.Markdown("### Scan for duplicate models")
        with gr.Row():
            with gr.Column():
                scan_dup_model_types_drop = gr.CheckboxGroup(
                    choices=model_types,
                    label="Model Types",
                    value=model_types
                )
        with gr.Row():
            with gr.Column(scale=2):
                cached_hash_ckb = gr.Checkbox(
                    label="Use Hash from Metadata (May have false-positives but can be useful if you've pruned models)",
                    value=False,
                    elem_id="ch_cached_hash_ckb"
                )
            with gr.Column():
                scan_dup_model_btn = gr.Button(
                    value="Scan",
                    variant="primary",
                    elem_id="ch_scan_dup_model_civitai_btn"
                )

        # with gr.Row():
        scan_dup_model_log_md = gr.HTML(
            value="Scanning takes time, just wait. Check console log for details",
            elem_id="ch_scan_dup_model_log_md"
        )

    # ====events====
    scan_dup_model_btn.click(
        duplicate_check.scan_for_dups,
        inputs=[
            scan_dup_model_types_drop,
            cached_hash_ckb
        ],
        outputs=scan_dup_model_log_md
    )

def check_new_versions_section(js_msg_txtbox):
    """ Check models' new version section """

    with gr.Column():
        gr.Markdown("### Check models' new version")
        with gr.Row():
            with gr.Column(scale=2):
                model_types_ckbg = gr.CheckboxGroup(
                    choices=model_types,
                    label="Model Types",
                    value=[
                        "ti", "hyper", "ckp", "lora", "lycoris"
                    ]
                )
                nsfw_preview_update_drop = gr.Dropdown(
                    label="Block NSFW Level Above",
                    choices=civitai.NSFW_LEVELS[1:],
                    value=util.get_opts("ch_nsfw_preview_threshold"),
                    elem_id="ch_nsfw_preview_dl_drop"
                )
        with gr.Row():
            with gr.Column(scale=2):
                check_models_new_version_btn = gr.Button(
                    value="Check New Version from Civitai",
                    variant="primary"
                )

        with gr.Row():
            with gr.Column():
                dl_new_version_log_md = gr.Markdown()
                check_models_new_version_log_md = gr.HTML(
                    "It takes time, just wait. Check console log for details"
                )

    # ====events====
    check_models_new_version_btn.click(
        model_action_civitai.check_models_new_version_to_md,
        inputs=model_types_ckbg,
        outputs=check_models_new_version_log_md
    )

    js_dl_model_new_version_btn = gr.Button(
        value="Download Model's new version",
        visible=False,
        elem_id="ch_js_dl_model_new_version_btn"
    )

    js_dl_model_new_version_btn.click(
        js_action_civitai.dl_model_new_version,
        inputs=[
            js_msg_txtbox,
            nsfw_preview_update_drop
        ],
        outputs=dl_new_version_log_md
    )
