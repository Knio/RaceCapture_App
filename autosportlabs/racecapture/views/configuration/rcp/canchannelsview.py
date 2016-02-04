import kivy
kivy.require('1.9.0')
import os
from kivy.metrics import sp
from kivy.app import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.switch import Switch
from kivy.uix.spinner import SpinnerOption
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from iconbutton import IconButton
from settingsview import SettingsSwitch
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseConfigView
from autosportlabs.racecapture.config.rcpconfig import *
from autosportlabs.racecapture.views.util.alertview import confirmPopup, choicePopup
from autosportlabs.racecapture.resourcecache.resourcemanager import ResourceCache
from fieldlabel import FieldLabel
from utils import *
from valuefield import FloatValueField, IntegerValueField
from mappedspinner import MappedSpinner

CAN_CHANNELS_VIEW_KV = 'autosportlabs/racecapture/views/configuration/rcp/canchannelsview.kv'

class LargeSpinnerOption(SpinnerOption):
    pass

class LargeMappedSpinner(MappedSpinner):
    pass
    
class LargeFieldLabel(FieldLabel):
    pass

class LargeIntegerValueField(IntegerValueField):
    pass

class LargeFloatValueField(FloatValueField):
    pass

class SectionBoxLayout(BoxLayout):
    pass

class CANChannelConfigView(BoxLayout):
    
    def __init__(self, index, can_channel_cfg, channels, max_sample_rate, can_filters, **kwargs):
        super(CANChannelConfigView, self).__init__(**kwargs)
        self._loaded = False
        self.register_event_type('on_editor_close')
        self.register_event_type('on_editor_commit')
        self.channel_index = index
        self.can_channel_cfg = can_channel_cfg
        self.channels = channels
        self.max_sample_rate = max_sample_rate
        self.can_filters = can_filters
        self.init_view()
        self._loaded = True

    def on_editor_close(self, *args):
        pass

    def on_editor_commit(self, *args):
        pass
        
    def on_cancel(self):
        self.dispatch('on_editor_close')        
    
    def on_commit(self):
        self.dispatch('on_editor_commit', self.channel_index, self.can_channel_cfg)
        self.dispatch('on_editor_close')
        
    def on_bit_mode(self, instance, value):
        if self._loaded:
            self.can_channel_cfg.bit_mode = self.ids.bitmode.active
            self.update_mapping_spinners()
    
    def on_sample_rate(self, instance, value):
        if self._loaded:        
            self.can_channel_cfg.sampleRate = instance.getValueFromKey(value)
        
    def on_can_bus_channel(self, instance, value):
        if self._loaded:
            self.can_channel_cfg.can_channel = instance.getValueFromKey(value)
        
    def on_can_id(self, instance, value):
        if self._loaded:
            self.can_channel_cfg.can_id = int(value)
        
    def on_bit_offset(self, instance, value):
        if self._loaded:        
            self.can_channel_cfg.bit_offset = instance.getValueFromKey(value)

    def on_bit_length(self, instance, value):
        if self._loaded:
            self.can_channel_cfg.bit_length = instance.getValueFromKey(value)
        
    def on_endian(self, instance, value):
        if self._loaded:
            self.can_channel_cfg.endian = instance.getValueFromKey(value)
        
    def on_multiplier(self, instance, value):
        if self._loaded:
            self.can_channel_cfg.multiplier = float(value)
        
    def on_adder(self, instance, value):
        if self._loaded:
            self.can_channel_cfg.adder = float(value)
        
    def on_filter(self, instance, value):
        if self._loaded:
            self.can_channel_cfg.conversion_filter_id = instance.getValueFromKey(value)
        
    def init_view(self):
        channel_editor = self.ids.chan_id
        channel_editor.on_channels_updated(self.channels)
        channel_editor.setValue(self.can_channel_cfg)
        
        sample_rate_spinner = self.ids.sr
        sample_rate_spinner.set_max_rate(self.max_sample_rate)
        sample_rate_spinner.setFromValue(self.can_channel_cfg.sampleRate)
        
        self.ids.can_bus_channel.setValueMap({0: '1', 1: '2'}, 0)
        
        self.ids.endian.setValueMap({0: 'Big (MSB)', 1: 'Little (LSB)'}, 0)
        
        self.ids.filters.setValueMap(self.can_filters.filters, self.can_filters.default_value)
        
        
        self.load_values()
        self.update_mapping_spinners()
        
    def load_values(self):

        #Channel Editor        
        channel_editor = self.ids.chan_id
        channel_editor.on_channels_updated(self.channels)
        channel_editor.setValue(self.can_channel_cfg)
        
        #Sample Rate
        sample_rate_spinner = self.ids.sr
        sample_rate_spinner.set_max_rate(self.max_sample_rate)        
        sample_rate_spinner.setFromValue(self.can_channel_cfg.sampleRate)
        
        #CAN Channel
        self.ids.can_bus_channel.setFromValue(self.can_channel_cfg.can_channel)
        
        #CAN ID
        self.ids.can_id.text = str(self.can_channel_cfg.can_id)
        
        #CAN offset
        self.ids.offset.text = str(self.can_channel_cfg.bit_offset)
        
        #CAN length
        self.ids.length.text = str(self.can_channel_cfg.bit_length)
        
        #Bit Mode
        self.ids.bitmode.active = self.can_channel_cfg.bit_mode
        
        #Endian
        self.ids.endian.setFromValue(self.can_channel_cfg.endian)
        
        #Multiplier
        self.ids.multiplier.text = str(self.can_channel_cfg.multiplier)
        
        #Adder
        self.ids.adder.text = str(self.can_channel_cfg.adder)
        
        #Conversion Filter ID
        self.ids.filters.setFromValue(self.can_channel_cfg.conversion_filter_id)
        
    def update_mapping_spinners(self):
        bit_mode = self.can_channel_cfg.bit_mode
        self.set_mapping_choices(bit_mode)
        
    def set_mapping_choices(self, bit_mode):
        choices = 63 if bit_mode else 7
        self.ids.offset.setValueMap(self.create_bit_choices(choices), 0)
        self.ids.length.setValueMap(self.create_bit_choices(1 + choices), 0)

    def create_bit_choices(self, max_choices):
        bit_choices = {}
        for i in range(0,max_choices + 1):
            bit_choices[i]=str(i)
        return bit_choices

class CANFilters(object):
    filters = None
    default_value = None
    def __init__(self, base_dir, **kwargs):
        super(CANFilters, self).__init__(**kwargs)
        self.load_CAN_filters(base_dir)

    
    def load_CAN_filters(self, base_dir):
        if self.filters != None:
            return
        try:
            self.filters = {}
            can_filters_json = open(os.path.join(base_dir, 'resource', 'settings', 'can_channel_filters.json'))
            can_filters = json.load(can_filters_json)['can_channel_filters']
            for k in sorted(can_filters.iterkeys()):
                if not self.default_value:
                    self.default_value = k 
                self.filters[int(k)] = can_filters[k] 
        except Exception as detail:
            raise Exception('Error loading CAN filters: ' + str(detail))

class CANChannelView(BoxLayout):
    channels = None
    can_channel_cfg = None
    max_sample_rate = 0
    channel_index = 0

    def __init__(self, channel_index, can_channel_cfg, max_sample_rate, channels, **kwargs):
        super(CANChannelView, self).__init__(**kwargs)
        self.channel_index = channel_index
        self.can_channel_cfg = can_channel_cfg
        self.max_sample_rate = max_sample_rate
        self.channels = channels
        self.register_event_type('on_delete_channel')
        self.register_event_type('on_customize_channel')
        self.register_event_type('on_modified')
        self.set_channel()
            
    def on_modified(self):
        pass

    def on_sample_rate(self, instance, value):
        self.can_channel_cfg.sampleRate = instance.getValueFromKey(value)
        self.dispatch('on_modified')
                    
    def on_delete_channel(self, channel_index):
        pass
    
    def on_customize_channel(self, channel_index):
        pass
    
    def on_delete(self):
        self.dispatch('on_delete_channel', self.channel_index)
    
    def on_customize(self):
        self.dispatch('on_customize_channel', self.channel_index)
        
    def set_channel(self):
        sample_rate_spinner = self.ids.sr
        sample_rate_spinner.set_max_rate(self.max_sample_rate)        
        sample_rate_spinner.setFromValue(self.can_channel_cfg.sampleRate)
        
        self.ids.channel_name.text = '{}'.format(self.can_channel_cfg.name)
        self.ids.can_id.text = '{}'.format(self.can_channel_cfg.can_id)
        self.ids.can_offset_len.text = u'{} ( {} )'.format(self.can_channel_cfg.bit_offset, self.can_channel_cfg.bit_length)
        sign = '-' if self.can_channel_cfg.adder < 0 else '+'
        self.ids.can_formula.text = u'\u00D7 {} {} {}'.format(self.can_channel_cfg.multiplier, sign, abs(self.can_channel_cfg.adder))
        self.ids.can_offset_len.text = u'{}({})'.format(self.can_channel_cfg.bit_offset, self.can_channel_cfg.bit_length)
        sign = '-' if self.can_channel_cfg.adder < 0 else '+'
        self.ids.can_formula.text = u'\u00D7 {} {} {}'.format(self.can_channel_cfg.multiplier, sign, abs(self.can_channel_cfg.adder))
        
class CANPresetResourceCache(ResourceCache):
    preset_url="http://race-capture.com/api/v1/can_presets"
    preset_name = 'can_presets'
    
    def __init__(self, settings, base_dir, **kwargs):
        default_preset_dir = os.path.join(base_dir, 'resource', self.preset_name)        
        super(CANPresetResourceCache, self).__init__(settings, self.preset_url, self.preset_name, default_preset_dir, **kwargs)    
    
class CANChannelsView(BaseConfigView):
    DEFAULT_CAN_SAMPLE_RATE = 1    
    can_channels_cfg = None
    max_sample_rate = 0
    can_grid = None
    can_channels_settings = None
    can_filters = None
    _popup = None
    
    def __init__(self, **kwargs):
        Builder.load_file(CAN_CHANNELS_VIEW_KV)
        super(CANChannelsView, self).__init__(**kwargs)
        self.register_event_type('on_config_updated')
        self.can_grid = self.ids.can_grid
        self._base_dir = kwargs.get('base_dir')
        
        can_channels_enable = self.ids.can_channels_enable
        can_channels_enable.bind(on_setting=self.on_can_channels_enabled)
        can_channels_enable.setControl(SettingsSwitch())
        self.update_view_enabled()
        self.can_filters = CANFilters(self._base_dir)
        self._resource_cache = None

    def get_resource_cache(self):
        if self._resource_cache is None:
            self._resource_cache = CANPresetResourceCache(self.settings, self._base_dir)
        return self._resource_cache
        
    def on_modified(self, *args):
        if self.can_channels_cfg:
            self.can_channels_cfg.stale = True
            self.dispatch('on_config_modified', *args)

    def on_can_channels_enabled(self, instance, value):
        if self.can_channels_cfg:
            self.can_channels_cfg.enabled = value
            self.dispatch('on_modified')
                    
    def on_config_updated(self, rc_cfg):
        can_channels_cfg = rc_cfg.can_channels
        max_sample_rate = rc_cfg.capabilities.sample_rates.sensor
        self.ids.can_channels_enable.setValue(can_channels_cfg.enabled)
        
        self.reload_can_channel_grid(can_channels_cfg, max_sample_rate)
        self.can_channels_cfg = can_channels_cfg
        self.max_sample_rate = max_sample_rate
        self.update_view_enabled()

    def update_view_enabled(self):
        add_disabled = True
        if self.can_channels_cfg:
            if len(self.can_channels_cfg.channels) < CAN_CHANNELS_MAX:
                add_disabled = False
                
        self.ids.add_can_channel.disabled = add_disabled
        
    def reload_can_channel_grid(self, can_channels_cfg, max_sample_rate):
        self.can_grid.clear_widgets()
        channel_count = len(can_channels_cfg.channels)
        for i in range(channel_count):
            can_channel_cfg = can_channels_cfg.channels[i]
            self.append_can_channel(i, can_channel_cfg, max_sample_rate)
        self.update_view_enabled()
        self.ids.list_msg.text = 'No Channels defined. Press (+) to map a CAN channel' if channel_count == 0 else ''

    def append_can_channel(self, index, can_channel_cfg, max_sample_rate):
        channel_view = CANChannelView(index, can_channel_cfg, max_sample_rate, self.channels)
        channel_view.bind(on_delete_channel=self.on_delete_channel)
        channel_view.bind(on_customize_channel=self.on_customize_channel)
        channel_view.bind(on_modified=self.on_modified)
        self.can_grid.add_widget(channel_view)
        
    def on_add_can_channel(self):
        if (self.can_channels_cfg):
            can_channel = CANChannel()
            can_channel.sampleRate = self.DEFAULT_CAN_SAMPLE_RATE
            new_channel_index = self.add_can_channel(can_channel)
            self._customize_channel(new_channel_index)

    def add_can_channel(self, can_channel):
        self.can_channels_cfg.channels.append(can_channel)
        new_channel_index = len(self.can_channels_cfg.channels) - 1
        self.append_can_channel(new_channel_index, can_channel, self.max_sample_rate)
        self.update_view_enabled()
        self.dispatch('on_modified')
        return new_channel_index
            
    def _delete_all_channels(self):
        del self.can_channels_cfg.channels[:]
        self.reload_can_channel_grid(self.can_channels_cfg, self.max_sample_rate)
        self.dispatch('on_modified')
        
    def _delete_can_channel(self, channel_index ):
        del self.can_channels_cfg.channels[channel_index]
        self.reload_can_channel_grid(self.can_channels_cfg, self.max_sample_rate)
        self.dispatch('on_modified')
        
    def on_delete_channel(self, instance, channel_index):
        popup = None 
        def _on_answer(instance, answer):
            if answer:
                self._delete_can_channel(channel_index)
            popup.dismiss()
        popup = confirmPopup('Confirm', 'Delete CAN Channel?', _on_answer)
        
    def _replace_config(self, to_cfg, from_cfg):
        to_cfg.__dict__.update(from_cfg.__dict__)
        
    def on_edited(self, instance, index, can_channel_cfg):
        self._replace_config(self.can_channels_cfg.channels[index], can_channel_cfg)
        self.reload_can_channel_grid(self.can_channels_cfg, self.max_sample_rate)
        self.dispatch('on_modified')

    def popup_dismissed(self, *args):
        self.reload_can_channel_grid(self.can_channels_cfg, self.max_sample_rate)
    
    def _customize_channel(self, channel_index):
        working_channel_cfg = copy(self.can_channels_cfg.channels[channel_index])
        content = CANChannelConfigView(channel_index, working_channel_cfg, self.channels, self.max_sample_rate, self.can_filters)
        content.bind(on_editor_commit=self.on_edited)
        content.bind(on_editor_close=lambda *args:popup.dismiss())
        popup = Popup(title="Customize CAN Channel", content=content, size_hint=(spct(0.75), spct(0.7)))
        popup.bind(on_dismiss=self.popup_dismissed)
        popup.open()
        
    def on_customize_channel(self, instance, channel_index):
        self._customize_channel(channel_index)

    def on_preset_selected(self, instance, preset_id):
        popup = None 
        def _on_answer(instance, answer):
            if answer == True:
                self._delete_all_channels()
            self._import_preset(preset_id)
            popup.dismiss()
            
        if len(self.can_channels_cfg.channels) > 0:
            popup = choicePopup('Confirm', 'Overwrite or append existing channels?', 'Overwrite', 'Append', _on_answer)
        else:
            self._import_preset(preset_id)
    
    def _import_preset(self, preset_id):
        resource_cache = self.get_resource_cache()
        preset = resource_cache.resources.get(preset_id)
        if preset:
            for channel_json in preset['channels']:
                new_channel = CANChannel()
                new_channel.fromJson(channel_json)
                self.add_can_channel(new_channel)
        
    def load_preset_view(self):
        content = PresetBrowserView(self.get_resource_cache())
        content.bind(on_preset_selected=self.on_preset_selected)
        content.bind(on_preset_close=lambda *args:popup.dismiss())
        popup = Popup(title='Import a preset configuration', content=content, size_hint=(0.5, 0.75))
        popup.bind(on_dismiss=self.popup_dismissed)
        popup.open()

class PresetItemView(BoxLayout):
    def __init__(self, preset_id, name, notes, image_path, **kwargs):
        super(PresetItemView, self).__init__(**kwargs)
        self.preset_id = preset_id
        self.ids.title.text = name
        self.ids.notes.text = notes
        self.ids.image.source = image_path
        self.register_event_type('on_preset_selected')
        
    def select_preset(self):
        self.dispatch('on_preset_selected', self.preset_id)

    def on_preset_selected(self, preset_id):
        pass
    
class PresetBrowserView(BoxLayout):
    presets = None
    
    def __init__(self, resource_cache, **kwargs):
        super(PresetBrowserView, self).__init__(**kwargs)
        self.register_event_type('on_preset_close')
        self.register_event_type('on_preset_selected')
        self.resource_cache = resource_cache
        self.init_view()
        
    def on_preset_close(self):
        pass
    
    def on_preset_selected(self, preset_id):
        pass
    
    def init_view(self):
        self.refresh_view()
        
    def refresh_view(self):
        for k,v in self.resource_cache.resources.iteritems():
            name = v.get('name', '')
            notes = v.get('notes', '')
            self.add_preset(k, name, notes)
        
    def add_preset(self, preset_id, name, notes):
        image_path = self.resource_cache.resource_image_paths.get(preset_id)
        preset_view = PresetItemView(preset_id, name, notes, image_path)
        preset_view.bind(on_preset_selected = self.preset_selected)
        self.ids.preset_grid.add_widget(preset_view)

    def preset_selected(self, instance, preset_id):
        self.dispatch('on_preset_selected', preset_id)
        self.dispatch('on_preset_close')
        
    def on_close(self, *args):
        self.dispatch('on_preset_close')