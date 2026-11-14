import unicodedata, statistics as st
import tiktoken
from tiktoken.load import load_tiktoken_bpe
import sentencepiece as spm
from mistral_common.tokens.tokenizers.tekken import Tekkenizer
SP = "venv/lib/python3.13/site-packages/"
L3 = r"(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?\p{L}+|\p{N}{1,3}| ?[^\s\p{L}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+"
L4 = r"""[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}]*[\p{Ll}\p{Lm}\p{Lo}\p{M}]+(?i:'s|'t|'re|'ve|'m|'ll|'d)?|[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}]+[\p{Ll}\p{Lm}\p{Lo}\p{M}]*(?i:'s|'t|'re|'ve|'m|'ll|'d)?|\p{N}{1,3}| ?[^\s\p{L}\p{N}]+[\r\n/]*|\s*[\r\n]+|\s+(?!\S)|\s+"""
def tk(path, pat, name):
    return tiktoken.Encoding(name=name, pat_str=pat, mergeable_ranks=load_tiktoken_bpe(SP+path), special_tokens={})
toks = {
 "Llama 3 (2024)": tk("llama_models/llama3/tokenizer.model", L3, "l3").encode,
 "Llama 4 (2025)": tk("llama_models/llama4/tokenizer.model", L4, "l4").encode,
 "Mistral Tekken (2024)": (lambda t, k=Tekkenizer.from_file(SP+"mistral_common/data/tekken_240911.json"): k.encode(t, bos=False, eos=False)),
 "Mistral 7B v1 (2023)": spm.SentencePieceProcessor(model_file=SP+"mistral_common/data/tokenizer.model.v1").encode,
}
S = [
("The doctor said I should take this medicine twice a day after meals.","डॉक्टर ने कहा कि मुझे यह दवा दिन में दो बार खाने के बाद लेनी चाहिए।","医生说我应该每天饭后吃两次这种药。","Bijîşk got ku divê ez vê dermanê rojê du caran piştî xwarinê bixwim."),
("My grandmother lives in a small village near the mountains.","मेरी दादी पहाड़ों के पास एक छोटे से गाँव में रहती हैं।","我的奶奶住在山附近的一个小村子里。","Dapîra min li gundekî biçûk nêzîkî çiyayan dijî."),
("The school will be closed tomorrow because of heavy snow.","भारी बर्फबारी के कारण कल स्कूल बंद रहेगा।","由于大雪，学校明天将关闭。","Ji ber berfa giran, dibistan dê sibê girtî be."),
("Please call me when you arrive at the airport.","जब आप हवाई अड्डे पर पहुँचें तो कृपया मुझे फ़ोन करें।","你到机场的时候请给我打电话。","Ji kerema xwe dema tu gihîştî balafirgehê li min bigere."),
("How much does a ticket to the city cost?","शहर का टिकट कितने का है?","去城里的票多少钱？","Bilêta bajêr bi çiqasî ye?"),
("Children need to drink clean water every day to stay healthy.","स्वस्थ रहने के लिए बच्चों को हर दिन साफ़ पानी पीना चाहिए।","孩子们每天都需要喝干净的水来保持健康。","Zarok divê her roj ava paqij vexwin da ku saxlem bimînin."),
("The government announced a new law about education last week.","सरकार ने पिछले हफ़्ते शिक्षा के बारे में एक नए कानून की घोषणा की।","政府上周宣布了一项关于教育的新法律。","Hikûmetê hefteya borî derbarê perwerdehiyê de qanûneke nû ragihand."),
("I am learning to cook my mother's favorite dish.","मैं अपनी माँ का पसंदीदा खाना बनाना सीख रहा हूँ।","我正在学做我妈妈最喜欢的菜。","Ez fêr dibim ku xwarina dayika xwe ya herî bijare çêkim."),
("If it rains on Saturday, we will stay at home and watch a movie.","अगर शनिवार को बारिश हुई तो हम घर पर रहेंगे और फ़िल्म देखेंगे।","如果星期六下雨，我们就待在家里看电影。","Eger roja şemiyê baran bibare, em ê li malê bimînin û fîlmekê temaşe bikin."),
("The library opens at nine in the morning and closes at six in the evening.","पुस्तकालय सुबह नौ बजे खुलता है और शाम छह बजे बंद होता है।","图书馆早上九点开门，晚上六点关门。","Pirtûkxane sibehê saet neh vedibe û êvarê saet şeş tê girtin."),
("My brother wants to become an engineer when he grows up.","मेरा भाई बड़ा होकर इंजीनियर बनना चाहता है।","我弟弟长大后想当一名工程师。","Birayê min dixwaze dema mezin bibe bibe endezyar."),
("Farmers are worried because there has been no rain this year.","किसान चिंतित हैं क्योंकि इस साल बारिश नहीं हुई है।","农民们很担心，因为今年没有下雨。","Cotkar bi fikar in ji ber ku îsal baran nebariye."),
]
def strip(t): return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
langs = ["English","Hindi","Mandarin","Kurmanji","Kurmanji, accents dropped"]
cols = list(zip(*S)); cols.append(tuple(strip(t) for t in cols[3]))
if __name__=="__main__": print(f"{"tokenizer"':24}" + "".join(f"{l[:14]:>16}" for l in langs))
for name, enc in toks.items():
    tot = [sum(len(enc(t)) for t in c) for c in cols]
    print(f"{name:24}" + "".join(f"{n:>9} {n/tot[0]:4.1f}x" for n in tot))
