from cProfile import label
import random
import gradio as gr
import modules.sd_samplers
import modules.scripts as scripts
from modules import shared
import json
import os
import shutil
import requests
import textwrap
from pprint import pprint
from modules.ui import gr_show
from collections import namedtuple
from pathlib import Path


def list_files_with_extension(folder_path, extension):
    files = [os.path.splitext(f)[0] for f in os.listdir(folder_path) if f.endswith(extension)]
    return files

def convert_to_json(file_list, json_file_path):
    data = {k:'<lora:' + k + ':1>' for k in file_list}
    with open(json_file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

# 設定資料夾路徑和要存放 JSON 檔案的路徑
folder_path = 'C:\SD\sd.webui\sd.webui\webui\models\Lora\place'
json_file_path = 'C:\SD\sd.webui\sd.webui\webui\extensions\sd_web_ui_preset_v\place.json'
extension_to_filter = '.info'  # 設定要過濾的副檔名

# 取得副檔名為 "info" 的檔案清單
info_files_list = list_files_with_extension(folder_path, extension_to_filter)

# 將檔案清單轉換成 JSON 並儲存
#convert_to_json(info_files_list, json_file_path)

#print(f"檔案已轉換為 {json_file_path}")

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

additional_config_source = "additional_components.json"
additional_config_target = "additional_configs.json"
presets_config_source = "preset_configuration.json"
presets_config_target = "presets.json"

file_path = scripts.basedir() # file_path is basedir
scripts_path = os.path.join(file_path, "scripts")
path_to_update_flag = os.path.join(scripts_path, update_flag)
is_update_available = False
if os.path.exists(path_to_update_flag):
    is_update_available = True
    source_path = os.path.join(file_path, presets_config_source)
    target_path = os.path.join(file_path, presets_config_target)
    if not os.path.exists(target_path):
        shutil.move(source_path, target_path)
        print(f"Created: {presets_config_target}")
    else:
        print(f"Not writing {presets_config_target}: config exists already")
    os.remove(path_to_update_flag)

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
        #self.save_config(self.settings_file, config)


    def __init__(self, *args, **kwargs):
        
        self.compinfo = namedtuple("CompInfo", ["component", "label", "elem_id", "kwargs"])

        #self.settings_file = "preset_configuration.json"
        self.settings_file = "presets.json"
        #self.additional_settings_file = "additional_components.json"
        self.additional_settings_file = "additional_configs.json"
        #self.additional_components_for_presets = self.get_config(self.additional_settings_file) #additionalComponents

        # Read saved settings
        PresetManager.all_presets = self.get_config(self.settings_file)
        PresetManager.size_presets = self.get_config(self.additional_settings_file)
        
        self.available_components = list(PresetManager.all_presets["Reset"].keys())
        self.available_size_components = list(PresetManager.size_presets["Width"].keys())
        
        if is_update_available:
            self.update_config()

        # components that pass through after_components
        self.all_components = []

        # Initialize
        self.component_map = {k: None for k in self.available_components}
        self.size_component_map = {k:None for k in self.available_size_components}
        #self.additional_components = [x for x in self.additional_components_map] # acts like available_components list for additional components

        # combine defaults and choices
        #self.component_map = {**self.component_map, **self.additional_components_map}
        #self.available_components = self.available_components + self.additional_components

        #色色大師設定
        self.hm_config_1 = "hm_config_1.json"
        self.hm_config_2 = "hm_config_2.json"
        self.hm_config_3 = "hm_config_3.json"
        self.hm_config_4 = "hm_config_4.json"
        self.hm_config_5 = "hm_config_5.json"
        self.hm_config_6 = "hm_config_6.json"

        self.localizations = "localizations\zh_TW.json"

        self.hm_config_1_component = self.get_config(self.hm_config_1)
        self.hm_config_2_component = self.get_config(self.hm_config_2)
        self.hm_config_3_component = self.get_config(self.hm_config_3)
        self.hm_config_4_component = self.get_config(self.hm_config_4)
        self.hm_config_5_component = self.get_config(self.hm_config_5)
        self.hm_config_6_component = self.get_config(self.hm_config_6)
        
        self.localizations_component = self.get_config2(self.localizations)

        self.hm1prompt = ""
        self.hm2prompt = ""
        self.hm3prompt = ""
        self.hm4prompt = ""
        self.hm5prompt = ""
        self.hm6prompt = ""

        #text value
        self.hm1btntext = ""
        self.hm2btntext = ""
        self.hm3btntext = ""
        self.hm4btntext = ""

        self.locked1 = ""
        self.locked2 = ""
        self.locked3 = ""
        self.locked4 = ""

        #隨機的face也要記下來 避免蓋掉
        self.faceprompt = ""

        self.allfuncprompt = ""

        #前一次的 cprompt
        self.oldcprompt=""
    
    def fakeinit(self, *args, **kwargs):
        """
        __init__ workaround, since some data is not available during instantiation, such as is_img2img, filename, etc.
        This method is called from .show(), as that's the first method ScriptRunner calls after handing some state dat (is_txt2img, is_img2img2)
        """
        #self.elm_prfx = f"{'txt2img' if self.is_txt2img else 'img2img'}"
        self.elm_prfx = "preset-v"


        # UI elements
        # class level
        # NOTE: Would love to use one component rendered twice, but gradio does not allow rendering twice, so I need one per page
        if self.is_txt2img:
            # quick set tab
            PresetManager.txt2img_preset_dropdown = gr.Dropdown(
                label="Presets",
                choices=list(PresetManager.all_presets.keys()),
                render = False,
                elem_id=f"{self.elm_prfx}_preset_qs_dd"
            )
            #else:
            # quick set tab
            PresetManager.img2img_preset_dropdown = gr.Dropdown(
                label="Presets",
                choices=list(PresetManager.all_presets.keys()),
                render = False,
                elem_id=f"{self.elm_prfx}_preset_qs_dd"
            )
            # size ddl
            PresetManager.txt2img_size_dropdown = gr.Dropdown(
                label="Size",
                choices=list(PresetManager.size_presets.keys()),
                render = False,
                elem_id=f"{self.elm_prfx}_size_qs_dd"
            )


            #按鈕版
            PresetManager.txt2img_preset1_btn = gr.Button(
                value="快速",
                label="Preset1",
                variant="primary",
                render = False,
                elem_id=f"{self.elm_prfx}_Preset1_btn"
            )
            PresetManager.txt2img_preset2_btn = gr.Button(
                value="優質",
                label="Preset2",
                variant="primary",
                render = False,
                elem_id=f"{self.elm_prfx}_Preset2_btn"
            )
            PresetManager.txt2img_preset3_btn = gr.Button(
                value="極優",
                label="Preset3",
                variant="primary",
                render = False,
                elem_id=f"{self.elm_prfx}_Preset3_btn"
            )

            PresetManager.txt2img_size1_btn = gr.Button(
                value="寬",
                label="Size1",
                variant="primary",
                render = False,
                elem_id=f"{self.elm_prfx}_size1_btn"
            )
            PresetManager.txt2img_size2_btn = gr.Button(
                value="高",
                label="Size2",
                variant="primary",
                render = False,
                elem_id=f"{self.elm_prfx}_size2_btn"
            )
            PresetManager.txt2img_size3_btn = gr.Button(
                value="方",
                label="Size3",
                variant="primary",
                render = False,
                elem_id=f"{self.elm_prfx}_size3_btn"
            )
            PresetManager.txt2img_prompt_btn = gr.Button(
                value="使用自訂提詞",
                label="hprompt",
                variant="primary",
                render = False,
                elem_id=f"{self.elm_prfx}_prompt_btn"
            )
            PresetManager.txt2img_radom_prompt_btn = gr.Button(
                value="隨機色色",
                label="randomprompt",
                variant="primary",
                render = False,
                elem_id=f"{self.elm_prfx}_randomprompt_btn"
            )

            #h_m 人物
            PresetManager.txt2img_hm1_dropdown = gr.Dropdown(
                label="人物",
                choices=list(self.hm_config_1_component.keys()),
                render = False,
                elem_id=f"{self.elm_prfx}_hm1_dd"
            )

            #h_m 姿勢
            PresetManager.txt2img_hm2_dropdown = gr.Dropdown(
                label="姿勢",
                choices=list(self.hm_config_2_component.keys()),
                render = False,
                elem_id=f"{self.elm_prfx}_hm2_dd"
            )

            #h_m 場景
            PresetManager.txt2img_hm3_dropdown = gr.Dropdown(
                label="場景",
                choices=list(self.hm_config_3_component.keys()),
                render = False,
                elem_id=f"{self.elm_prfx}_hm3_dd"
            )

            #h_m 衣服
            PresetManager.txt2img_hm4_dropdown = gr.Dropdown(
                label="衣服",
                choices=list(self.hm_config_4_component.keys()),
                render = False,
                elem_id=f"{self.elm_prfx}_hm4_dd"
            )

            #h_m 表情
            PresetManager.txt2img_hm5_dropdown = gr.Dropdown(
                label="表情",
                choices=list(self.hm_config_5_component.keys()),
                render = False,
                elem_id=f"{self.elm_prfx}_hm5_dd"
            )

            #h_m 細節
            PresetManager.txt2img_hm6_dropdown = gr.Dropdown(
                label="細節",
                choices=list(self.hm_config_6_component.keys()),
                render = False,
                elem_id=f"{self.elm_prfx}_hm6_dd"
            )

            #隨機色色設定
            PresetManager.randset1_chk =gr.Checkbox(
                label="不使用人物lora",
                render = False,
                container = False,
                elem_id=f"{self.elm_prfx}_randset1_chk"
            )
            PresetManager.randset2_chk =gr.Checkbox(
                label="不使用姿勢lora",
                render = False,
                container = False,
                elem_id=f"{self.elm_prfx}_randset2_chk"
            )
            PresetManager.randset3_chk =gr.Checkbox(
                label="人物lora使用時，不使用衣服lora",
                render = False,
                container = False,
                elem_id=f"{self.elm_prfx}_randset3_chk"
            )
            PresetManager.randset4_chk =gr.Checkbox(
                label="不使用場景lora",
                render = False,
                container = False,
                elem_id=f"{self.elm_prfx}_randset4_chk"
            )

            #功能性調節
            PresetManager.func1_chk =gr.Checkbox(
                label="climax",
                render = False,
                container = False,
                elem_id=f"{self.elm_prfx}_func1_chk"
            )
            PresetManager.func2_chk =gr.Checkbox(
                label="Hands",
                render = False,
                container = False,
                elem_id=f"{self.elm_prfx}_func2_chk"
            )
            PresetManager.func3_chk =gr.Checkbox(
                label="pussy",
                render = False,
                container = False,
                elem_id=f"{self.elm_prfx}_func3_chk"
            )
            PresetManager.func4_chk =gr.Checkbox(
                label="ass",
                render = False,
                container = False,
                elem_id=f"{self.elm_prfx}_func4_chk"
            )
            PresetManager.func5_chk =gr.Checkbox(
                label="nipples",
                render = False,
                container = False,
                elem_id=f"{self.elm_prfx}_func5_chk"
            )
            PresetManager.func6_chk =gr.Checkbox(
                label="thighs",
                render = False,
                container = False,
                elem_id=f"{self.elm_prfx}_func6_chk"
            )
            PresetManager.func7_chk =gr.Checkbox(
                label="body",
                render = False,
                container = False,
                elem_id=f"{self.elm_prfx}_func7_chk"
            )
            PresetManager.func8_chk =gr.Checkbox(
                label="skin",
                render = False,
                container = False,
                elem_id=f"{self.elm_prfx}_func8_chk"
            )
            PresetManager.func9_chk =gr.Checkbox(
                label="ugly bastard",
                render = False,
                container = False,
                elem_id=f"{self.elm_prfx}_func9_chk"
            )
            PresetManager.func10_chk =gr.Checkbox(
                label="more detail",
                render = False,
                container = False,
                elem_id=f"{self.elm_prfx}_func10_chk"
            )
            PresetManager.func11_chk =gr.Checkbox(
                label="less detail",
                render = False,
                container = False,
                elem_id=f"{self.elm_prfx}_func11_chk"
            )
            PresetManager.func12_chk =gr.Checkbox(
                label="quality",
                render = False,
                container = False,
                elem_id=f"{self.elm_prfx}_func12_chk"
            )
            PresetManager.func13_chk =gr.Checkbox(
                label="realistic",
                render = False,
                container = False,
                elem_id=f"{self.elm_prfx}_func13_chk"
            )

            #後製
            PresetManager.affunc1_chk =gr.Checkbox(
                label="pussy",
                render = False,
                container = False,
                elem_id=f"{self.elm_prfx}_affunc1_chk"
            )
            PresetManager.affunc2_chk =gr.Checkbox(
                label="ass",
                render = False,
                container = False,
                elem_id=f"{self.elm_prfx}_affunc2_chk"
            )
            PresetManager.affunc3_chk =gr.Checkbox(
                label="breast",
                render = False,
                container = False,
                elem_id=f"{self.elm_prfx}_affunc3_chk"
            )
            PresetManager.affunc4_chk =gr.Checkbox(
                label="pussy 2",
                render = False,
                container = False,
                elem_id=f"{self.elm_prfx}_affunc4_chk"
            )
            PresetManager.affunc5_chk =gr.Checkbox(
                label="pubic hair",
                render = False,
                container = False,
                elem_id=f"{self.elm_prfx}_affunc5_chk"
            )
            #PresetManager.affunc6_chk =gr.Checkbox(
            #    label="face",
            #    render = False,
            #    container = False,
            #    elem_id=f"{self.elm_prfx}_affunc6_chk"
            #)

            #鎖定
            PresetManager.txt2img_lock1_btn = gr.Button(
                value="",
                label="lock1",
                variant="primary",
                render = False,
                elem_id=f"{self.elm_prfx}_lock1_btn"
            )
            PresetManager.txt2img_lock2_btn = gr.Button(
                value="",
                label="lock2",
                variant="primary",
                render = False,
                elem_id=f"{self.elm_prfx}_lock2_btn"
            )
            PresetManager.txt2img_lock3_btn = gr.Button(
                value="",
                label="lock3",
                variant="primary",
                render = False,
                elem_id=f"{self.elm_prfx}_lock3_btn"
            )
            #中文輸入框
            PresetManager.txt2img_cprompt_txt = gr.Textbox(lines=4, placeholder="可輸入中文描述", label="Ollama Prompt", elem_id=f"{self.elm_prfx}_cprompt_txt")
            PresetManager.txt2img_cprompt_btn = gr.Button(
                value="送出",
                label="cpromptbtn",
                variant="primary",
                render = False,
                elem_id=f"{self.elm_prfx}_cprompt_btn"
            )

        self.input_prompt = PresetManager.txt2img_cprompt_txt

        # instance level
        # quick set tab
        #self.stackable_check = gr.Checkbox(value=True, label="Stackable", elem_id=f"{self.elm_prfx}_stackable_check", render=False)
        #self.save_as = gr.Text(render=False, label="Quick Save", elem_id=f"{self.elm_prfx}_save_qs_txt")
        #self.save_button = gr.Button(value="Save", variant="secondary", render=False, visible=False, elem_id=f"{self.elm_prfx}_save_qs_bttn")

        self.hide_all_button = gr.Button(value="簡易版", variant="primary", render=False, visible=True, elem_id=f"{self.elm_prfx}_hide_all_bttn")
        self.show_all_button = gr.Button(value="一般版", variant="primary", render=False, visible=True, elem_id=f"{self.elm_prfx}_show_all_bttn")

        self.lock_seed_button = gr.Button(value="鎖定seed", variant="primary", render=False, visible=True, elem_id=f"{self.elm_prfx}_lock_seed_bttn")
        self.rdn_seed_button = gr.Button(value="隨機seed", variant="primary", render=False, visible=True, elem_id=f"{self.elm_prfx}_rdn_seed_bttn")

    def title(self):
        return "Presets"

    def show(self, is_img2img):
        self.fakeinit()
        return True
        if self.ui_first == "sampler":
            if shared.opts.samplers_in_dropdown:
                self.before_component_label = "Sampling method"
            else:
                self.before_component_label = "Sampling Steps"
            return True
        else:
            self.before_component_label = self.positon_manager
            return True

    def before_component(self, component, **kwargs):
        pass
    def _before_component(self, component, **kwargs):
        # Define location of where to show up
        #if kwargs.get("elem_id") == "":#f"{'txt2img' if self.is_txt2img else 'img2img'}_progress_bar":
        #print(kwargs.get("label") == self.before_component_label, "TEST", kwargs.get("label"))
        #if kwargs.get("label") == self.before_component_label:
            with gr.Accordion(label="簡易設定", open = True, elem_id=f"{'txt2img' if self.is_txt2img else 'img2img'}_preset_manager_accordion"):
                #with gr.Row(equal_height = True):
                    #if self.is_txt2img:
                        #PresetManager.txt2img_preset_dropdown.render()
                    #else:
                        #PresetManager.img2img_preset_dropdown.render()
                with gr.Row(equal_height = True):
                    PresetManager.txt2img_preset1_btn.render()
                    PresetManager.txt2img_preset2_btn.render()
                    PresetManager.txt2img_preset3_btn.render()
                    #with gr.Column(elem_id=f"{self.elm_prfx}_ref_del_col_qs"):
                        #self.stackable_check.render()
                #with gr.Row(equal_height = True):
                    #PresetManager.txt2img_size_dropdown.render()
                with gr.Row(equal_height = True):
                    PresetManager.txt2img_size1_btn.render()
                    PresetManager.txt2img_size2_btn.render()
                    PresetManager.txt2img_size3_btn.render()
            with gr.Row(equal_height = True):
                self.hide_all_button.render()
                self.show_all_button.render()
            with gr.Row(equal_height = True):
                PresetManager.txt2img_prompt_btn.render()
            with gr.Accordion(label="色色設定", open = False, elem_id=f"{'txt2img' if self.is_txt2img else 'img2img'}_h_setting_accordion"):
                with gr.Accordion(label="提詞設定", open = False, elem_id=f"{'txt2img' if self.is_txt2img else 'img2img'}_prompt_setting_accordion"):
                    with gr.Row(equal_height = True):
                        PresetManager.txt2img_hm1_dropdown.render() 
                    with gr.Row(equal_height = True):
                        PresetManager.txt2img_hm2_dropdown.render() 
                    with gr.Row(equal_height = True):
                        PresetManager.txt2img_hm3_dropdown.render() 
                    with gr.Row(equal_height = True):
                        PresetManager.txt2img_hm4_dropdown.render() 
                    with gr.Row(equal_height = True):
                        PresetManager.txt2img_hm5_dropdown.render() 
                    with gr.Row(equal_height = True):
                        PresetManager.txt2img_hm6_dropdown.render() 
                with gr.Accordion(label="隨機設定", open = False, elem_id=f"{'txt2img' if self.is_txt2img else 'img2img'}_randh_setting_accordion"):
                    PresetManager.randset1_chk.render()
                    PresetManager.randset2_chk.render()
                    PresetManager.randset3_chk.render()
                    PresetManager.randset4_chk.render()
                with gr.Accordion(label="細節設定", open = False, elem_id=f"{'txt2img' if self.is_txt2img else 'img2img'}_f_setting_accordion"):
                    with gr.Row(equal_height = True):
                        PresetManager.func1_chk.render()
                        PresetManager.func2_chk.render()
                    with gr.Row(equal_height = True):
                        PresetManager.func3_chk.render() 
                        PresetManager.func4_chk.render()
                    with gr.Row(equal_height = True):
                        PresetManager.func5_chk.render()
                        PresetManager.func6_chk.render() 
                    with gr.Row(equal_height = True):
                        PresetManager.func7_chk.render() 
                        PresetManager.func8_chk.render() 
                    with gr.Row(equal_height = True):
                        PresetManager.func9_chk.render() 
                        PresetManager.func10_chk.render() 
                    with gr.Row(equal_height = True):
                        PresetManager.func11_chk.render() 
                        PresetManager.func12_chk.render() 
                    with gr.Row(equal_height = True):
                        PresetManager.func13_chk.render() 
                #with gr.Accordion(label="後製設定", open = False, elem_id=f"{'txt2img' if self.is_txt2img else 'img2img'}_af_setting_accordion"):
                    #with gr.Row(equal_height = True):
                        #self.lock_seed_button.render()
                        #self.rdn_seed_button.render()
                    #with gr.Row(equal_height = True):
                        #PresetManager.affunc1_chk.render()
                        #PresetManager.affunc2_chk.render()
                    #with gr.Row(equal_height = True):
                        #PresetManager.affunc3_chk.render() 
                        #PresetManager.affunc4_chk.render()
                    #with gr.Row(equal_height = True):
                        #PresetManager.affunc5_chk.render()
            with gr.Accordion(label="鎖定[人物][姿勢]", open = True, elem_id=f"{'txt2img' if self.is_txt2img else 'img2img'}_lock_accordion"):
                with gr.Row(equal_height = True):
                    PresetManager.txt2img_lock1_btn.render()
                    PresetManager.txt2img_lock2_btn.render()
            with gr.Row(equal_height = True):
                PresetManager.txt2img_radom_prompt_btn.render()
            with gr.Row(equal_height = True):
                PresetManager.txt2img_cprompt_txt.render()
            with gr.Row(equal_height = True):
                PresetManager.txt2img_cprompt_btn.render()

    def after_component(self, component, **kwargs):
        if hasattr(component, "label") or hasattr(component, "elem_id"):
            self.all_components.append(self.compinfo(
                                                      component=component,
                                                      label=component.label if hasattr(component, "label") else None,
                                                      elem_id=component.elem_id if hasattr(component, "elem_id") else None,
                                                      kwargs=kwargs
                                                     )
                                      )
            #if hasattr(component, "label"):
                #print(f"label:{component.label}")
            #if hasattr(component, "elem_id"):
                #print(f"elem_id:{component.elem_id}")

        label = kwargs.get("label")
        ele = kwargs.get("elem_id")
        # TODO: element id
        #if label in self.component_map or label in self.additional_components_map:# and ele == self.additional_components["additionalComponents"]) or (ele == self.additional_components["additionalComponents"]):
        if label in self.component_map:# and ele == self.additional_components["additionalComponents"]) or (ele == self.additional_components["additionalComponents"]):
            #!Hack to remove conflict between main Prompt and hr Prompt
            if self.component_map[label] is None:
                self.component_map.update({component.label: component})


        if label in self.size_component_map:
            if self.size_component_map[label] is None:
                self.size_component_map.update({component.label: component})
        # 提示詞
        if ele == "txt2img_prompt": 
            self.prompt_component = component

        if ele == "txt2img_generation_info_button" or ele == "img2img_generation_info_button":
            self._ui()

        if ele == "txt2img_styles_dialog":
            self._before_component("")

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
            #PresetManager.txt2img_size_dropdown.change(
            #    fn=self.fetch_valid_values_from_size,
            #    inputs=[PresetManager.txt2img_size_dropdown] + [self.size_component_map[comp_name] for comp_name in list(x for x in self.available_size_components if self.size_component_map[x] is not None)],
            #    outputs=[self.size_component_map[comp_name] for comp_name in list(x for x in self.available_size_components if self.size_component_map[x] is not None)],
            #)
            PresetManager.txt2img_preset1_btn.click(
                fn=self.fetch_valid_values_from_preset1,
                outputs=[self.component_map[comp_name] for comp_name in list(x for x in self.available_components if self.component_map[x] is not None)],
            ) 
            PresetManager.txt2img_preset2_btn.click(
                fn=self.fetch_valid_values_from_preset2,
                outputs=[self.component_map[comp_name] for comp_name in list(x for x in self.available_components if self.component_map[x] is not None)],
            )    
            PresetManager.txt2img_preset3_btn.click(
                fn=self.fetch_valid_values_from_preset3,
                outputs=[self.component_map[comp_name] for comp_name in list(x for x in self.available_components if self.component_map[x] is not None)],
            )               
            PresetManager.txt2img_size1_btn.click(
                fn=self.fetch_valid_values_from_size1,
                outputs=[self.size_component_map[comp_name] for comp_name in list(x for x in self.available_size_components if self.size_component_map[x] is not None)],
            )
            PresetManager.txt2img_size2_btn.click(
                fn=self.fetch_valid_values_from_size2,
                outputs=[self.size_component_map[comp_name] for comp_name in list(x for x in self.available_size_components if self.size_component_map[x] is not None)],
            )
            PresetManager.txt2img_size3_btn.click(
                fn=self.fetch_valid_values_from_size3,
                outputs=[self.size_component_map[comp_name] for comp_name in list(x for x in self.available_size_components if self.size_component_map[x] is not None)],
            )
            #色色大師功能區
            PresetManager.txt2img_prompt_btn.click(
                fn=self.fetch_valid_values_from_prompt,
                outputs=self.prompt_component
            )
            PresetManager.txt2img_radom_prompt_btn.click(
                fn=self.h_m_random_prompt,
                inputs=[PresetManager.randset1_chk,PresetManager.randset2_chk,PresetManager.randset3_chk,PresetManager.randset4_chk],
                outputs=[self.prompt_component, PresetManager.txt2img_lock1_btn, PresetManager.txt2img_lock2_btn]
            )
            #hm
            PresetManager.txt2img_hm1_dropdown.change(
                fn=self.hm1_setting,
                inputs=[PresetManager.txt2img_hm1_dropdown,self.prompt_component],
                outputs=[self.prompt_component, PresetManager.txt2img_lock1_btn]
            )
            PresetManager.txt2img_hm2_dropdown.change(
                fn=self.hm2_setting,
                inputs=[PresetManager.txt2img_hm2_dropdown,self.prompt_component],
                outputs=[self.prompt_component, PresetManager.txt2img_lock2_btn]
            )
            PresetManager.txt2img_hm3_dropdown.change(
                fn=self.hm3_setting,
                inputs=[PresetManager.txt2img_hm3_dropdown,self.prompt_component],
                outputs=self.prompt_component
            )
            PresetManager.txt2img_hm4_dropdown.change(
                fn=self.hm4_setting,
                inputs=[PresetManager.txt2img_hm4_dropdown,self.prompt_component],
                outputs=self.prompt_component
            )
            PresetManager.txt2img_hm5_dropdown.change(
                fn=self.hm5_setting,
                inputs=[PresetManager.txt2img_hm5_dropdown,self.prompt_component],
                outputs=self.prompt_component
            )
            PresetManager.txt2img_hm6_dropdown.change(
                fn=self.hm6_setting,
                inputs=[PresetManager.txt2img_hm6_dropdown, self.prompt_component],
                outputs=self.prompt_component
            )
            #細節功能
            detailinput = [self.prompt_component,PresetManager.func1_chk,PresetManager.func2_chk,PresetManager.func3_chk,PresetManager.func4_chk,PresetManager.func5_chk,PresetManager.func6_chk,PresetManager.func7_chk,PresetManager.func8_chk,PresetManager.func9_chk,PresetManager.func10_chk,PresetManager.func11_chk,PresetManager.func12_chk,PresetManager.func13_chk]
            PresetManager.func1_chk.change(
                fn=self.func_setting,
                inputs=detailinput,
                outputs=self.prompt_component
            )
            PresetManager.func2_chk.change(
                fn=self.func_setting,
                inputs=detailinput,
                outputs=self.prompt_component
            )
            PresetManager.func3_chk.change(
                fn=self.func_setting,
                inputs=detailinput,
                outputs=self.prompt_component
            )
            PresetManager.func4_chk.change(
                fn=self.func_setting,
                inputs=detailinput,
                outputs=self.prompt_component
            )
            PresetManager.func5_chk.change(
                fn=self.func_setting,
                inputs=detailinput,
                outputs=self.prompt_component
            )
            PresetManager.func6_chk.change(
                fn=self.func_setting,
                inputs=detailinput,
                outputs=self.prompt_component
            )
            PresetManager.func7_chk.change(
                fn=self.func_setting,
                inputs=detailinput,
                outputs=self.prompt_component
            )
            PresetManager.func8_chk.change(
                fn=self.func_setting,
                inputs=detailinput,
                outputs=self.prompt_component
            )
            PresetManager.func9_chk.change(
                fn=self.func_setting,
                inputs=detailinput,
                outputs=self.prompt_component
            )
            PresetManager.func10_chk.change(
                fn=self.func_setting,
                inputs=detailinput,
                outputs=self.prompt_component
            )
            PresetManager.func11_chk.change(
                fn=self.func_setting,
                inputs=detailinput,
                outputs=self.prompt_component
            )
            PresetManager.func12_chk.change(
                fn=self.func_setting,
                inputs=detailinput,
                outputs=self.prompt_component
            )
            PresetManager.func13_chk.change(
                fn=self.func_setting,
                inputs=detailinput,
                outputs=self.prompt_component
            )
            #後製功能
            #PresetManager.affunc1_chk.change(
                #fn=self.affunc_setting,
                #inputs=[self.component_map["ad_prompt"],PresetManager.affunc1_chk,PresetManager.affunc2_chk,PresetManager.affunc3_chk,PresetManager.affunc4_chk,PresetManager.affunc5_chk],
                #outputs=[self.component_map["Enable ADetailer"],self.component_map["ADetailer model"],self.component_map["ad_prompt"]]
            #)
            #PresetManager.affunc2_chk.change(
                #fn=self.affunc_setting,
                #inputs=[self.component_map["ad_prompt"],PresetManager.affunc1_chk,PresetManager.affunc2_chk,PresetManager.affunc3_chk,PresetManager.affunc4_chk,PresetManager.affunc5_chk],
                #outputs=[self.component_map["Enable ADetailer"],self.component_map["ADetailer model"],self.component_map["ad_prompt"]]
            #)
            #PresetManager.affunc3_chk.change(
                #fn=self.affunc_setting,
                #inputs=[self.component_map["ad_prompt"],PresetManager.affunc1_chk,PresetManager.affunc2_chk,PresetManager.affunc3_chk,PresetManager.affunc4_chk,PresetManager.affunc5_chk],
                #outputs=[self.component_map["Enable ADetailer"],self.component_map["ADetailer model"],self.component_map["ad_prompt"]]
            #)
            #PresetManager.affunc4_chk.change(
                #fn=self.affunc_setting,
                #inputs=[self.component_map["ad_prompt"],PresetManager.affunc1_chk,PresetManager.affunc2_chk,PresetManager.affunc3_chk,PresetManager.affunc4_chk,PresetManager.affunc5_chk],
                #outputs=[self.component_map["Enable ADetailer"],self.component_map["ADetailer model"],self.component_map["ad_prompt"]]
            #)
            #PresetManager.affunc5_chk.change(
                #fn=self.affunc_setting,
                #inputs=[self.component_map["ad_prompt"],PresetManager.affunc1_chk,PresetManager.affunc2_chk,PresetManager.affunc3_chk,PresetManager.affunc4_chk,PresetManager.affunc5_chk],
                #outputs=[self.component_map["Enable ADetailer"],self.component_map["ADetailer model"],self.component_map["ad_prompt"]]
            #)
            #鎖定
            PresetManager.txt2img_lock1_btn.click(
                fn=self.prompt_lock1,
                outputs=[PresetManager.txt2img_hm1_dropdown, PresetManager.txt2img_lock1_btn]
            ) 
            PresetManager.txt2img_lock2_btn.click(
                fn=self.prompt_lock2,
                outputs=[PresetManager.txt2img_hm2_dropdown, PresetManager.txt2img_lock2_btn]
            )
            #ai輸出
            #self.input_prompt.change(self.input_prompt, self.input_prompt, None)
            PresetManager.txt2img_cprompt_btn.click(
                fn=self.cprompt_send,
                inputs=[self.prompt_component, self.input_prompt],
                outputs=self.prompt_component
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
    
    def get_config2(self, path, open_mode='r'):
        file = os.path.join(PresetManager.BASEDIR, path)
        try:
            with open(file, open_mode, encoding='utf-8') as f:
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
    
    def fetch_valid_values_from_size(self, selection, *comps_vals):
        print(selection)
        print(comps_vals)
        return [
            PresetManager.size_presets[selection][comp_name] 
                if (comp_name in PresetManager.size_presets[selection] 
                    and (
                        True if not hasattr(self.size_component_map[comp_name], "choices") 
                            else 
                            True if PresetManager.size_presets[selection][comp_name] in self.size_component_map[comp_name].choices 
                                else False 
                        ) 
                    ) 
                else 
                    self.size_component_map[comp_name].value
                for i, comp_name in enumerate(list(x for x in self.available_size_components if self.size_component_map[x] is not None and hasattr(self.size_component_map[x], "value")))]
    
    #按鈕版
    def fetch_valid_values_from_preset1(self):
        return [
            PresetManager.all_presets["Quick"][comp_name] 
                if (comp_name in PresetManager.all_presets["Quick"] 
                    and (
                        True if not hasattr(self.component_map[comp_name], "choices") 
                            else 
                            True if PresetManager.all_presets["Quick"][comp_name] in self.component_map[comp_name].choices 
                                else False 
                        ) 
                    ) 
                else 
                    self.component_map[comp_name].value
                for i, comp_name in enumerate(list(x for x in self.available_components if self.component_map[x] is not None and hasattr(self.component_map[x], "value")))]
    
    def fetch_valid_values_from_preset2(self):
        return [
            PresetManager.all_presets["Better"][comp_name] 
                if (comp_name in PresetManager.all_presets["Better"] 
                    and (
                        True if not hasattr(self.component_map[comp_name], "choices") 
                            else 
                            True if PresetManager.all_presets["Better"][comp_name] in self.component_map[comp_name].choices 
                                else False 
                        ) 
                    ) 
                else 
                    self.component_map[comp_name].value
                for i, comp_name in enumerate(list(x for x in self.available_components if self.component_map[x] is not None and hasattr(self.component_map[x], "value")))]
    
    def fetch_valid_values_from_preset3(self):
        return [
            PresetManager.all_presets["Great"][comp_name] 
                if (comp_name in PresetManager.all_presets["Great"] 
                    and (
                        True if not hasattr(self.component_map[comp_name], "choices") 
                            else 
                            True if PresetManager.all_presets["Great"][comp_name] in self.component_map[comp_name].choices 
                                else False 
                        ) 
                    ) 
                else 
                    self.component_map[comp_name].value
                for i, comp_name in enumerate(list(x for x in self.available_components if self.component_map[x] is not None and hasattr(self.component_map[x], "value")))]
    
    def fetch_valid_values_from_size1(self):
        return [
            PresetManager.size_presets["Width"][comp_name] 
                if (comp_name in PresetManager.size_presets["Width"] 
                    and (
                        True if not hasattr(self.size_component_map[comp_name], "choices") 
                            else 
                            True if PresetManager.size_presets["Width"][comp_name] in self.size_component_map[comp_name].choices 
                                else False 
                        ) 
                    ) 
                else 
                    self.size_component_map[comp_name].value
                for i, comp_name in enumerate(list(x for x in self.available_size_components if self.size_component_map[x] is not None and hasattr(self.size_component_map[x], "value")))]
    
    def fetch_valid_values_from_size2(self):
        return [
            PresetManager.size_presets["Height"][comp_name] 
                if (comp_name in PresetManager.size_presets["Height"] 
                    and (
                        True if not hasattr(self.size_component_map[comp_name], "choices") 
                            else 
                            True if PresetManager.size_presets["Height"][comp_name] in self.size_component_map[comp_name].choices 
                                else False 
                        ) 
                    ) 
                else 
                    self.size_component_map[comp_name].value
                for i, comp_name in enumerate(list(x for x in self.available_size_components if self.size_component_map[x] is not None and hasattr(self.size_component_map[x], "value")))]
    
    def fetch_valid_values_from_size3(self):
        return [
            PresetManager.size_presets["Square"][comp_name] 
                if (comp_name in PresetManager.size_presets["Square"] 
                    and (
                        True if not hasattr(self.size_component_map[comp_name], "choices") 
                            else 
                            True if PresetManager.size_presets["Square"][comp_name] in self.size_component_map[comp_name].choices 
                                else False 
                        ) 
                    ) 
                else 
                    self.size_component_map[comp_name].value
                for i, comp_name in enumerate(list(x for x in self.available_size_components if self.size_component_map[x] is not None and hasattr(self.size_component_map[x], "value")))]
    
    #自訂提詞
    def fetch_valid_values_from_prompt(self):
        self.prompt_component.value = "nsfw++++,"
        self.prompt_component.value += self.hm1prompt
        self.prompt_component.value += self.hm2prompt
        self.prompt_component.value += self.hm3prompt
        self.prompt_component.value += self.hm4prompt
        self.prompt_component.value += self.hm5prompt
        self.prompt_component.value += self.hm6prompt
        self.prompt_component.value += self.allfuncprompt
        return self.prompt_component.value
    
    #隨機
    def h_m_random_prompt(self,rs1,rs2,rs3,rs4):
        self.prompt_component.value = "nsfw++++,"
        chruse = False
        btn1text = ""
        btn2text = ""

        if(self.locked1 == ""):
            self.hm1btntext = ""
            if(self.hm1prompt==""):
                if(rs1 == False):
                    if(random.randint(0,100) > 20):
                        self.hm1btntext = list(self.hm_config_1_component)[random.randint(0,len(self.hm_config_1_component)-1)]
                        try:
                            btn1text = self.localizations_component[self.hm1btntext]
                        except:
                            btn1text = self.hm1btntext
                        self.prompt_component.value += self.hm_config_1_component[self.hm1btntext] + ","
                        chruse = True
            else:
                self.prompt_component.value += self.hm1prompt
        else:
            self.prompt_component.value += self.hm1prompt
            btn1text = "鎖定:"
            try:
                btn1text += self.localizations_component[self.hm1btntext]
            except:
                btn1text += self.hm1btntext

        if(self.locked2 == ""):
            self.hm2btntext = ""
            if(self.hm2prompt==""):
                if(rs2 == False):
                    self.hm2btntext = list(self.hm_config_2_component)[random.randint(0,len(self.hm_config_2_component)-1)]
                    try:
                        btn2text = self.localizations_component[self.hm2btntext]
                    except:
                        btn2text = self.hm2btntext
                    self.prompt_component.value += self.hm_config_2_component[self.hm2btntext] + ","
                else:
                    self.hm2btntext = list(self.hm_config_2_component)[random.randint(0,10)]
                    try:
                        btn2text = self.localizations_component[self.hm2btntext]
                    except:
                        btn2text = self.hm2btntext
                    self.prompt_component.value += self.hm_config_2_component[self.hm2btntext] + ","
            else:
                self.prompt_component.value += self.hm2prompt
        else:
            self.prompt_component.value += self.hm2prompt
            btn2text = "鎖定:"
            try:
                btn2text += self.localizations_component[self.hm2btntext]
            except:
                btn2text += self.hm2btntext        

        if(self.hm3prompt==""):
            if(rs4 == False):
                rnd3 = random.randint(0,100)
                if(rnd3 > 80):
                    self.prompt_component.value += "indoor,"
                elif(rnd3 > 60):
                    self.prompt_component.value += "outdoor,"
                elif(rnd3 > 20):
                    self.prompt_component.value += self.hm_config_3_component[list(self.hm_config_3_component)[random.randint(0,len(self.hm_config_3_component)-1)]] + ","
        else:
            self.prompt_component.value += self.hm3prompt
        
        if(self.hm4prompt==""):
            if(chruse):
                if(rs3):
                    self.prompt_component.value +=""
                else:
                    if(random.randint(0,100) > 50):
                        self.prompt_component.value += self.hm_config_4_component[list(self.hm_config_4_component)[random.randint(0,len(self.hm_config_4_component)-1)]] + ","
                    else:
                        self.prompt_component.value += "nude+++,"
        else:
            self.prompt_component.value += self.hm4prompt

        #AD用的  避免臉跑掉
        self.faceprompt=""
        if(self.hm5prompt==""):
            #前25個後面太奇怪了
            if(random.randint(0,100) > 50):
                self.faceprompt = self.hm_config_5_component[list(self.hm_config_5_component)[random.randint(0,25)]] + ","
                self.prompt_component.value += self.faceprompt
        else:
            self.prompt_component.value += self.hm5prompt
            self.faceprompt = self.hm5prompt

        #隨機 不使用 其他
        if(self.hm6prompt==""):
            self.prompt_component.value += ""
            #self.prompt_component.value += self.hm_config_6_component[list(self.hm_config_6_component)[random.randint(0,2)]] + ","
        else:
            self.prompt_component.value += self.hm6prompt

        self.prompt_component.value += self.allfuncprompt

        return [self.prompt_component.value, btn1text, btn2text]
    
    #自訂1
    def hm1_setting(self, selection, oldprompt):
        if(selection == ""):
            selection = "random"
        oldhmprompt = self.hm1prompt
        self.hm1prompt = ""
        btntext = ""
        #自行異動
        if(self.hm1btntext != selection):
            self.locked1 = ""
            if(selection != "random"):
                self.hm1prompt = self.hm_config_1_component[selection] + ","
                self.hm1btntext = selection
                if(self.locked1 == "Y" ):
                    btntext = "鎖定:"
                try:
                    btntext += self.localizations_component[self.hm1btntext]
                except:
                    btntext += self.hm1btntext
            if(oldhmprompt!=""):
                oldprompt = oldprompt.replace(oldhmprompt, self.hm1prompt)
            else:
                oldprompt += "," + self.hm1prompt
        else:
            if(selection != "random"):
                self.hm1prompt = self.hm_config_1_component[selection] + ","
            if(self.locked1 == "Y" ):
                btntext = "鎖定:"
            try:
                btntext += self.localizations_component[self.hm1btntext]
            except:
                btntext += self.hm1btntext
        return [oldprompt,btntext]

    #自訂2
    def hm2_setting(self, selection, oldprompt):
        if(selection == ""):
            selection = "random"
        oldhmprompt = self.hm2prompt
        self.hm2prompt = ""
        btntext = ""
        #自行異動
        if(self.hm2btntext != selection):
            self.locked2 = ""
            if(selection != "random"):
                self.hm2prompt = self.hm_config_2_component[selection] + ","
                self.hm2btntext = selection
                try:
                    btntext = self.localizations_component[self.hm2btntext]
                except:
                    btntext = self.hm2btntext
            if(oldhmprompt!=""):
                oldprompt = oldprompt.replace(oldhmprompt, self.hm2prompt)
            else:
                oldprompt += "," + self.hm2prompt
        else:
            if(selection != "random"):
                self.hm2prompt = self.hm_config_2_component[selection] + ","
            if(self.locked2 == "Y" ):
                btntext = "鎖定:"
            try:
                btntext += self.localizations_component[self.hm2btntext]
            except:
                btntext += self.hm2btntext
        return [oldprompt,btntext]

    #自訂3
    def hm3_setting(self, selection, oldprompt):
        oldhmprompt = self.hm3prompt
        self.hm3prompt = ""
        if(selection != "random"):
            self.hm3prompt = self.hm_config_3_component[selection] + ","
        if(oldhmprompt!=""):
            oldprompt = oldprompt.replace(oldhmprompt, self.hm3prompt)
        else:
            oldprompt += "," + self.hm3prompt
        return oldprompt

    #自訂4
    def hm4_setting(self, selection, oldprompt):
        oldhmprompt = self.hm4prompt
        self.hm4prompt = ""
        if(selection != "random"):
            self.hm4prompt = self.hm_config_4_component[selection] + ","
        if(oldhmprompt!=""):
            oldprompt = oldprompt.replace(oldhmprompt, self.hm4prompt)
        else:
            oldprompt += "," + self.hm4prompt
        return oldprompt

    #自訂5
    def hm5_setting(self, selection, oldprompt):
        oldhmprompt = self.hm5prompt
        self.hm5prompt = ""
        if(selection != "random"):
            self.hm5prompt = self.hm_config_5_component[selection] + ","
        if(oldhmprompt!=""):
            oldprompt = oldprompt.replace(oldhmprompt, self.hm5prompt)
        else:
            oldprompt += "," + self.hm5prompt
        return oldprompt

    #自訂6
    def hm6_setting(self, selection, oldprompt):
        oldhmprompt = self.hm6prompt
        self.hm6prompt = ""
        if(selection != "random"):
            self.hm6prompt = self.hm_config_6_component[selection] + ","
        if(oldhmprompt!=""):
            oldprompt = oldprompt.replace(oldhmprompt, self.hm6prompt)
        else:
            oldprompt += "," + self.hm6prompt
        return oldprompt
    
    #細節
    def func_setting(self, oldprompt,fv1,fv2,fv3,fv4,fv5,fv6,fv7,fv8,fv9,fv10,fv11,fv12,fv13):
        self.allfuncprompt = ""
        oldprompt = oldprompt.replace("(Girl trembling with sexual climax)++,", "")
        oldprompt = oldprompt.replace("<lyco:GoodHands-beta2:1.4>,", "")
        oldprompt = oldprompt.replace("<lora:gape_cpt_v04.10:0.6>,", "")
        oldprompt = oldprompt.replace("<lora:AGFIN:0.8>,AG,", "")
        oldprompt = oldprompt.replace("<lora:BigBeautifulNipples_v1:1>,", "")
        oldprompt = oldprompt.replace("thick thighs,", "")
        oldprompt = oldprompt.replace("<lora:ChihunHentai_20230709225610-000004:1>,ChihunHentai,", "")
        oldprompt = oldprompt.replace("<lora:Shinyskin-000018:0.6>,", "")
        oldprompt = oldprompt.replace("<lora:ugly_bastard_v5.4a:1.5>,", "")
        oldprompt = oldprompt.replace("OverallDetail++,", "")
        oldprompt = oldprompt.replace("<lora:add_detail:0.2>,", "")
        oldprompt = oldprompt.replace("(masterpiece,best quality:1.4),", "")
        oldprompt = oldprompt.replace("RAW photo,realistic,", "")

        if(fv1):
            self.allfuncprompt += "(Girl trembling with sexual climax)++,"
        if(fv2):
            self.allfuncprompt += "<lyco:GoodHands-beta2:1.4>,"
        if(fv3):
            self.allfuncprompt += "<lora:gape_cpt_v04.10:0.6>,"
        if(fv4):
            self.allfuncprompt += "<lora:AGFIN:0.8>,AG,"
        if(fv5):
            self.allfuncprompt += "<lora:BigBeautifulNipples_v1:1>,"
        if(fv6):
            self.allfuncprompt += "thick thighs,"
        if(fv7):
            self.allfuncprompt += "<lora:ChihunHentai_20230709225610-000004:1>,ChihunHentai,"
        if(fv8):
            self.allfuncprompt += "<lora:Shinyskin-000018:0.6>,"
        if(fv9):
            self.allfuncprompt += "<lora:ugly_bastard_v5.4a:1.5>,"
        if(fv10):
            self.allfuncprompt += "OverallDetail++,"
        if(fv11):
            self.allfuncprompt += "<lora:add_detail:0.2>,"
        if(fv12):
            self.allfuncprompt += "(masterpiece,best quality:1.4),"
        if(fv13):
            self.allfuncprompt += "RAW photo,realistic,"
        oldprompt += self.allfuncprompt
        return oldprompt
    
    #後製
    def affunc_setting(self, oldprompt,afv1,afv2,afv3,afv4,afv5):
        isuse = False
        model1 = "None"
        mprompt1 = ""
        if(afv1 or afv2 or afv3 or afv4 or afv5):
            isuse = True
            model1 = "person_yolov8n-seg.pt"

        mprompt1 += self.faceprompt
        if(afv1):
            mprompt1 += "<lora:Pussy_Lotte_v5n:0.8>,pussy"
        if(afv2):
            mprompt1 += "lora:AGFIN:0.8>,AG,"
        if(afv3):
            mprompt1 += "<lora:BigBeautifulNipples_v1:1>,"
        if(afv4):
            mprompt1 += "<lora:pussy:1.2>,pussy,"
        if(afv5):
            mprompt1 += "pubic hair,"
        return [isuse,model1,mprompt1]
    
    def prompt_lock1(self):
        if(self.locked1 == ""):
            self.locked1 = "Y"
            self.hm1prompt = self.hm1btntext
            try:
                btntext = "鎖定:" + self.localizations_component[self.hm1btntext]
            except:
                btntext = "鎖定:" + self.hm1btntext
        else:
            self.locked1 = ""
            try:
                btntext = self.localizations_component[self.hm1btntext]
            except:
                btntext = self.hm1btntext
            self.hm1prompt = ""
        return [self.hm1prompt, btntext]
    
    def prompt_lock2(self):
        if(self.locked2 == ""):
            self.locked2 = "Y"
            self.hm2prompt = self.hm2btntext
            try:
                btntext = "鎖定:" + self.localizations_component[self.hm2btntext]
            except:
                btntext = "鎖定:" + self.hm2btntext
        else:
            self.locked2 = ""
            btntext = self.hm2prompt
            self.hm2prompt = ""
        return [self.hm2prompt, btntext]
    
    def cprompt_send(self, oldprompt, input_prompt):
        generated_texts = []
        generated_texts = self.send_request(input_prompt)
        #clear beafore
        oldprompt = oldprompt.replace(self.oldcprompt, '')
        self.oldcprompt = ''
        for text in generated_texts:
            self.oldcprompt += text
        self.oldcprompt = self.oldcprompt.replace(", ", ",") 
        oldprompt = oldprompt + ',' + self.oldcprompt
        print(f"llama3: {self.oldcprompt}")
        return oldprompt
    
    def send_request(self, input_prompt, **kwargs):
        prime_directive = textwrap.dedent("""\
            Act as a prompt maker with the following guidelines:               
            - Break keywords by commas.
            - Provide high-quality, non-verbose, coherent, brief, concise, and not superfluous prompts.
            - Focus solely on the visual elements of the picture; avoid art commentaries or intentions.
            - Construct the prompt with the component format:
            1. Start with the subject and keyword description.
            2. Follow with motion keyword description.
            3. Follow with scene keyword description.
            4. Finish with background and keyword description.
            - Limit yourself to no more than 20 keywords per component  
            - Include all the keywords from the user's request verbatim as the main subject of the response.
            - Be varied and creative.
            - Always reply on the same line and no more than 100 words long. 
            - Do not enumerate or enunciate components.
            - Create creative additional information in the response.    
            - Response in English.                                                    
            The followin is an illustartive example for you to see how to construct a prompt your prompts should follow this format but always coherent to the subject worldbuilding or setting and cosider the elemnts relationship.
            Example:
            Demon Hunter,Cyber City,A Demon Hunter,standing,lone figure,glow eyes,deep purple light,cybernetic exoskeleton,sleek,metallic,glowing blue accents,energy weapons,Fighting Demon,grotesque creature,twisted metal,glowing red eyes,sharp claws,towering structures,shrouded haze,shimmering energy,                            
            Make a prompt for the following Subject:
            """)
        data = {
                'model': 'impactframes/llama3_ifai_sd_prompt_mkr_q4km:latest',
                'messages': [
                    {"role": "system", "content": prime_directive},
                    {"role": "user", "content": input_prompt}
                ],  
            }
        headers = kwargs.get('headers', {"Content-Type": "application/json"})
        base_url = f'http://127.0.0.1:11434/v1/chat/completions'
        response = requests.post(base_url, headers=headers, json=data)

        if response.status_code == 200:
            return response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
        else:
            print(f"Error: Request failed with status code {response.status_code}")
            return []

    def local_request_restart(self):
        "Restart button"
        shared.state.interrupt()
        shared.state.need_restart = True



