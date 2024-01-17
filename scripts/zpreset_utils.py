import gradio as gr
import modules.sd_samplers
import modules.scripts as scripts
from modules import shared
import json
import os
import shutil
from pprint import pprint
from modules.ui import gr_show
from collections import namedtuple
from pathlib import Path

#  *********     versioning     *****
repo = None
version_map = {
    'https://github.com/vladmandic/automatic':"vlads",
    None: "a1111"
    }
#Test for a1111 or vlads, vlad had the courtesy to set a variable
if hasattr(shared, "url"):
    repo = version_map[getattr(shared, "url")]
else:
    repo = "a1111"

try:
    import launch

    if not launch.is_installed("colorama"):
            launch.run_pip("install colorama")
except:
    pass

try:
    from colorama import just_fix_windows_console, Fore, Style
    just_fix_windows_console()
except:
    pass

update_flag = "preset_manager_update_check"

presets_config_source = "preset_configuration.json"
presets_config_target = "presets.json"

file_path = scripts.basedir() # file_path is basedir
scripts_path = os.path.join(file_path, "scripts")
path_to_update_flag = os.path.join(scripts_path, update_flag)
is_update_available = False

class PresetManager(scripts.Script):

    BASEDIR = scripts.basedir()

    def update_component_name(self, preset, oldval, newval):
        if preset.get(oldval) is not None:
            preset[newval] = preset.pop(oldval)

    def update_config(self):
        """This is a as per need method that will change per need"""
        component_remap = {
            "Highres. fix": "Hires. fix",
            "Firstpass width": "Upscaler",
            "Firstpass height": "Upscale by",
            "Sampling Steps": "Sampling steps",
            "Hires. steps": "Hires steps"
            }
        
        if repo == "vlads":
            component_remap.update({
                "Hires. fix" : "Hires fix"
            })

        
        config = self.get_config(self.settings_file)
        for preset in config.values():
            for old_val, new_val in component_remap.items():
                self.update_component_name(preset, old_val, new_val)
                    
        #PresetManager.all_presets = config
        self.save_config(self.settings_file, config)


    def __init__(self, *args, **kwargs):
        
        self.compinfo = namedtuple("CompInfo", ["component", "label", "elem_id", "kwargs"])

        #self.settings_file = "preset_configuration.json"
        self.settings_file = "presets.json"

        self.available_components = [
            "Prompt", #! must create filter for hr prompt and neg prompt using elem_id in after component 5/28/23
            "Negative prompt",
            "Sampling steps",
            "Sampling method",
            "Width",
            "Height",
            "Restore faces",
            "Tiling",
            "Hires. fix" if repo != "vlads" else "Hires fix",#NewNew Vlads #!update config needs a version check
            "Highres. fix",#old
            "Upscaler",#new
            "Upscale by",#new
            "Hires. steps",#NewOld,
            "Hires steps",#NewNew
            "Resize width to",#New
            "Resize height to",#New
            "Hires sampling method",#Newest 5/27/23
            "Seed",
            "Extra",
            "Variation seed",
            "Variation strength",
            "Resize seed from width",
            "Resize seed from height",
            "Firstpass width",#old now is upscaler
            "Firstpass height",#old now is upscale by
            "Denoising strength",
            "Batch count",
            "Batch size",
            "CFG Scale",
            "Image CFG Scale",
            "Refiner",
	        "Checkpoint",
	        "Switch at",
	        "Enable ADetailer",
            "Script",
            "Input directory",
            "Output directory",
            "Inpaint batch mask directory (required for inpaint batch processing only)",
            "Resize mode",
            "Scale",
            "Mask blur",
            "Mask transparency",
            "Mask mode",
            "Masked content",
            "Inpaint area",
            "Only masked padding, pixels",
        ]
        
        if is_update_available:
            self.update_config()

        # components that pass through after_components
        self.all_components = []
 
        # Read saved settings
        PresetManager.all_presets = self.get_config(self.settings_file)

        # Initialize
        self.component_map = {k: None for k in self.available_components}

        # combine defaults and choices
        self.component_map = {**self.component_map}
    
    def fakeinit(self, *args, **kwargs):
        self.elm_prfx = "preset-util"
        PresetManager.txt2img_preset_dropdown = gr.Dropdown(
            label="Presets",
            choices=list(PresetManager.all_presets.keys()),
            render = False,
            elem_id=f"{self.elm_prfx}_preset_qs_dd"
        )

    def title(self):
        return "Presets"

    def show(self):
        self.fakeinit()
        return True

    def before_component(self, component, **kwargs):
        pass
    def _before_component(self, component, **kwargs):
        with gr.Accordion(label="Preset Manager", open = True, elem_id=f"{'txt2img' if self.is_txt2img else 'img2img'}_preset_manager_accordion"):
            with gr.Row(equal_height = True):
                PresetManager.txt2img_preset_dropdown.render()
               
    def after_component(self, component, **kwargs):
        if hasattr(component, "label") or hasattr(component, "elem_id"):
            self.all_components.append(self.compinfo(
                                                      component=component,
                                                      label=component.label if hasattr(component, "label") else None,
                                                      elem_id=component.elem_id if hasattr(component, "elem_id") else None,
                                                      kwargs=kwargs
                                                     )
                                      )
            
        label = kwargs.get("label")
        ele = kwargs.get("elem_id")
        # TODO: element id
        if label in self.component_map:
            print(label)
            if self.component_map[label] is None:
                self.component_map.update({component.label: component})
        
        if ele == "txt2img_generation_info_button":
            self._before_component("")
        self._ui()

    def ui(self, *args):
        pass

    def _ui(self):
        # Conditional for class members
        if self.is_txt2img:
            # Quick Set Tab
            PresetManager.txt2img_preset_dropdown.change(
                fn=self.fetch_valid_values_from_preset,
                inputs=[PresetManager.txt2img_preset_dropdown] + [self.component_map[comp_name] for comp_name in list(x for x in self.available_components if self.component_map[x] is not None)],
                outputs=[self.component_map[comp_name] for comp_name in list(x for x in self.available_components if self.component_map[x] is not None)],
            )
        else:
            # Quick Set Tab
            PresetManager.img2img_preset_dropdown.change(
                fn=self.fetch_valid_values_from_preset,
                inputs=[PresetManager.img2img_preset_dropdown] + [self.component_map[comp_name] for comp_name in list(x for x in self.available_components if self.component_map[x] is not None)],
                outputs=[self.component_map[comp_name] for comp_name in list(x for x in self.available_components if self.component_map[x] is not None)],
            )

    def f_b_syncer(self):
        """
        ?Front/Backend synchronizer?
        Not knowing what else to call it, simple idea, rough to figure out. When updating choices on the front-end, back-end isn't updated, make them both match
        https://github.com/gradio-app/gradio/discussions/2848
        """
        self.inspect_dd.choices = [str(x) for x in self.all_components]
        return [gr.update(choices=[str(x) for x in self.all_components]), gr.Button.update(visible=False)]

    
    def inspection_formatter(self, x):
        comp = self.all_components[x]
        text = f"Component Label: {comp.label}\nElement ID: {comp.elem_id}\nComponent: {comp.component}\nAll Info Handed Down: {comp.kwargs}"
        return text


    def run(self, p, *args):
        pass

    def get_config(self, path, open_mode='r'):
        file = os.path.join(PresetManager.BASEDIR, path)
        try:
            with open(file, open_mode) as f:
                as_dict = json.load(f) 
        except FileNotFoundError as e:
            print(f"{e}\n{file} not found, check if it exists or if you have moved it.")
        return as_dict 
    

    def fetch_valid_values_from_preset(self, selection, *comps_vals):
        print(selection)
        print(comps_vals)
        return [
            PresetManager.all_presets[selection][comp_name] 
                if (comp_name in PresetManager.all_presets[selection] 
                    and (
                        True if not hasattr(self.component_map[comp_name], "choices") 
                            else 
                            True if PresetManager.all_presets[selection][comp_name] in self.component_map[comp_name].choices 
                                else False 
                        ) 
                ) 
                else 
                    self.component_map[comp_name].value
                for i, comp_name in enumerate(list(x for x in self.available_components if self.component_map[x] is not None and hasattr(self.component_map[x], "value")))]
    

