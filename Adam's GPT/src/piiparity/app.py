"""Local-only Gradio UI. No input logging, examples cache or public share tunnel."""
import os
os.environ['GRADIO_ANALYTICS_ENABLED']='False'
from .system import LANGUAGES,MODES,compare,highlights
EXAMPLES=[
('English','Mira Patel lives in London. Email mira@example.com or call +1-202-555-0100.'),
('Kurmanji (experimental)','Navê min Roj Azad e. Ez li Amedê dijîm. E-name: roj@example.com.'),
('Hindi','मेरा नाम आशा शर्मा है। मैं दिल्ली में रहती हूँ। ईमेल: asha@example.com।'),
('Simplified Chinese','我叫李明，住在北京。我的邮箱是 liming@example.com。'),
('Spanish','Me llamo Lucía Torres y vivo en Madrid. Correo: lucia@example.com.'),
('Turkish',"Benim adım Deniz Yılmaz. Ankara şehrinde yaşıyorum. E-posta: deniz@example.com.")]

def analyze(text,language,mode):
    import gradio as gr
    try:
        if language not in LANGUAGES:raise ValueError('Choose a listed language.')
        if mode not in MODES:raise ValueError('Choose a listed detector.')
        results=compare(text,LANGUAGES[language]);selected=results[mode]
    except ValueError as e:raise gr.Error(str(e)) from None
    except Exception:raise gr.Error('AI inference unavailable. Check the local model installation; no fallback result was substituted.') from None
    status='Processed locally. Check the highlighted spans and compare the outputs.'
    if language.startswith('Kurmanji'):status+=' Kurmanji: experimental transfer, no validated language-specific accuracy.'
    return (highlights(text,selected['entities']),selected['redacted_text'],
        results['Regex']['redacted_text'],results['AI']['redacted_text'],results['Hybrid']['redacted_text'],
        selected['entities'],status)

def build_app():
    import gradio as gr
    css='''#hero {max-width:1000px;margin:auto} .gradio-container {max-width:1100px!important} footer {display:none!important}'''
    with gr.Blocks(title='PIIParity | Multilingual privacy lab',theme=gr.themes.Soft(primary_hue='teal',neutral_hue='slate'),css=css,analytics_enabled=False) as demo:
        gr.Markdown('# PIIParity\n### Spot personal information. Compare protection across languages.\nPaste a **fictional** paragraph, choose a detector, and inspect what it finds.',elem_id='hero')
        gr.Markdown('**Research prototype:** missed information can remain. Do not paste private messages. Kurmanji is experimental; no language has independently validated accuracy yet.')
        with gr.Row():
            language=gr.Dropdown(list(LANGUAGES),value='English',label='Text language',info='For labeling results only; no automatic detection or translation.')
            mode=gr.Radio(list(MODES),value='Hybrid',label='Detector for highlights and output')
        text=gr.Textbox(label='Your fictional text',lines=4,placeholder='Mira Patel lives in London. Email mira@example.com.',max_lines=8)
        button=gr.Button('Detect & compare',variant='primary')
        status=gr.Markdown('Local model · original-text offsets · no public upload')
        with gr.Row():
            marked=gr.HighlightedText(label='Detected entities',show_legend=True,color_map={'PERSON':'#bbf7d0','LOCATION':'#bfdbfe','EMAIL':'#fde68a','PHONE':'#fecdd3'})
            redacted=gr.Textbox(label='Selected redacted output',lines=4,interactive=False,show_copy_button=True)
        with gr.Accordion('Compare all three detectors',open=True):
            base=gr.Textbox(label='Regex baseline',interactive=False)
            ai=gr.Textbox(label='AI model',interactive=False)
            hybrid=gr.Textbox(label='Hybrid AI + regex',interactive=False)
        with gr.Accordion('Entity offsets, source and raw score',open=False):
            entities=gr.JSON(label='Original Unicode code-point spans; scores are not calibrated')
        gr.Examples([[t,l,'Hybrid'] for l,t in EXAMPLES],inputs=[text,language,mode],cache_examples=False)
        gr.Markdown('The language selector records your choice; it does not improve or guarantee model coverage. Model weights download separately. Inference stays on this computer; the local browser/server holds text transiently. No application text log or database. Up to 1,500 characters and 320 model tokens; longer input is rejected.')
        button.click(analyze,[text,language,mode],[marked,redacted,base,ai,hybrid,entities,status],api_name='analyze',concurrency_limit=1)
    return demo

def main():
    build_app().queue(max_size=8).launch(server_name='127.0.0.1',server_port=7860,share=False,show_error=False,quiet=True)
if __name__=='__main__':main()
