from app import create_app
from app.extensions import db
from app.models import LearningItem, ListeningClip, ReadingPassage

app = create_app()

HIRAGANA = [
    ("あ", "a"), ("い", "i"), ("う", "u"), ("え", "e"), ("お", "o"),
    ("か", "ka"), ("き", "ki"), ("く", "ku"), ("け", "ke"), ("こ", "ko"),
    ("さ", "sa"), ("し", "shi"), ("す", "su"), ("せ", "se"), ("そ", "so"),
    ("た", "ta"), ("ち", "chi"), ("つ", "tsu"), ("て", "te"), ("と", "to"),
    ("な", "na"), ("に", "ni"), ("ぬ", "nu"), ("ね", "ne"), ("の", "no"),
    ("は", "ha"), ("ひ", "hi"), ("ふ", "fu"), ("へ", "he"), ("ほ", "ho"),
    ("ま", "ma"), ("み", "mi"), ("む", "mu"), ("め", "me"), ("も", "mo"),
    ("や", "ya"), ("ゆ", "yu"), ("よ", "yo"), ("ら", "ra"), ("り", "ri"),
    ("る", "ru"), ("れ", "re"), ("ろ", "ro"), ("わ", "wa"), ("を", "wo"), ("ん", "n"),
]

KATAKANA = [
    ("ア", "a"), ("イ", "i"), ("ウ", "u"), ("エ", "e"), ("オ", "o"),
    ("カ", "ka"), ("キ", "ki"), ("ク", "ku"), ("ケ", "ke"), ("コ", "ko"),
    ("サ", "sa"), ("シ", "shi"), ("ス", "su"), ("セ", "se"), ("ソ", "so"),
    ("タ", "ta"), ("チ", "chi"), ("ツ", "tsu"), ("テ", "te"), ("ト", "to"),
    ("ナ", "na"), ("ニ", "ni"), ("ヌ", "nu"), ("ネ", "ne"), ("ノ", "no"),
    ("ハ", "ha"), ("ヒ", "hi"), ("フ", "fu"), ("ヘ", "he"), ("ホ", "ho"),
    ("マ", "ma"), ("ミ", "mi"), ("ム", "mu"), ("メ", "me"), ("モ", "mo"),
    ("ヤ", "ya"), ("ユ", "yu"), ("ヨ", "yo"), ("ラ", "ra"), ("リ", "ri"),
    ("ル", "ru"), ("レ", "re"), ("ロ", "ro"), ("ワ", "wa"), ("ヲ", "wo"), ("ン", "n"),
]

GRAMMAR = [
    ("State of being", "state-of-being", "Use だ or です to identify or describe something.", "Noun + だ / です", "私は学生です。", "Basics"),
    ("Particle は", "particle-wa", "は marks the topic: what the sentence is about.", "Topic は comment", "今日は暑いです。", "Particles"),
    ("Particle が", "particle-ga", "が marks the subject or highlights new information.", "Subject が predicate", "猫がいます。", "Particles"),
    ("Particle を", "particle-wo", "を marks the direct object of an action.", "Object を verb", "水を飲みます。", "Particles"),
    ("Particle に", "particle-ni", "に marks destination, time, or indirect target.", "Place/Time に verb", "学校に行きます。", "Particles"),
    ("Particle で", "particle-de", "で marks where an action happens or the means used.", "Place/Tool で action", "図書館で勉強します。", "Particles"),
    ("Particle の", "particle-no", "の links nouns and often shows possession or description.", "Noun の noun", "私の本です。", "Particles"),
    ("い-adjectives", "i-adjectives", "い-adjectives end in い and can directly describe nouns.", "い-adjective + noun", "新しい本を読みます。", "Adjectives"),
    ("な-adjectives", "na-adjectives", "な-adjectives use な before nouns and です at sentence end.", "な-adjective な noun", "静かな町です。", "Adjectives"),
    ("ru-verbs", "ru-verbs", "Many ru-verbs end in る and drop る before some endings.", "食べる -> 食べます", "毎朝パンを食べます。", "Verbs"),
    ("u-verbs", "u-verbs", "u-verbs change their final sound before endings.", "飲む -> 飲みます", "お茶を飲みます。", "Verbs"),
    ("Negative verbs", "negative-verbs", "Negative forms say that an action does not happen.", "食べる -> 食べない", "肉を食べません。", "Conjugation"),
    ("Past tense", "past-tense", "Past tense places actions or states before now.", "行く -> 行った / 行きました", "昨日学校に行きました。", "Conjugation"),
    ("Te-form", "te-form", "The te-form links actions and supports requests.", "食べる -> 食べて", "名前を書いてください。", "Conjugation"),
    ("Polite form", "polite-form", "ます and です make basic sentences polite.", "verb stem + ます", "日本語を勉強します。", "Basics"),
]

VOCAB = [
    ("water", "水", "みず", "water", "noun,basic"),
    ("student", "学生", "がくせい", "student", "noun,people"),
    ("Japan", "日本", "にほん", "Japan", "place"),
    ("book", "本", "ほん", "book", "noun"),
    ("to drink", "飲む", "のむ", "to drink", "verb"),
    ("to study", "勉強する", "べんきょうする", "to study", "verb"),
]

KANJI = [
    ("日", "にち, ひ", "sun; day"),
    ("本", "ほん, もと", "book; origin"),
    ("人", "じん, ひと", "person"),
    ("水", "すい, みず", "water"),
    ("学", "がく", "study"),
]

CONJUGATIONS = [
    ("食べる -> polite past", "食べる", "食べました"),
    ("見る -> polite past", "見る", "見ました"),
    ("行く -> te-form", "行く", "行って"),
    ("飲む -> negative", "飲む", "飲まない"),
    ("する -> polite present", "する", "します"),
    ("来る -> past negative", "来る", "来なかった"),
]


def upsert(slug, **values):
    item = LearningItem.query.filter_by(slug=slug).first()
    if not item:
        item = LearningItem(slug=slug)
        db.session.add(item)
    for key, value in values.items():
        setattr(item, key, value)
    return item


def seed():
    db.create_all()
    for char, romaji in HIRAGANA:
        upsert(
            f"hiragana-{romaji}",
            item_type="kana",
            title=f"Hiragana {char}",
            japanese=char,
            reading=romaji,
            meaning=romaji,
            explanation=f"{char} is the hiragana for {romaji}.",
            tags="hiragana,kana",
        )
    for char, romaji in KATAKANA:
        upsert(
            f"katakana-{romaji}",
            item_type="kana",
            title=f"Katakana {char}",
            japanese=char,
            reading=romaji,
            meaning=romaji,
            explanation=f"{char} is the katakana for {romaji}.",
            tags="katakana,kana",
        )
    for title, slug, explanation, pattern, example, tag in GRAMMAR:
        upsert(
            slug,
            item_type="grammar",
            title=title,
            explanation=explanation,
            pattern=pattern,
            example_sentence=example,
            jlpt_level="N5",
            difficulty=1,
            source_name="Tae Kim's Guide to Japanese Grammar",
            source_url="https://guidetojapanese.org/learn/grammar",
            tags=tag,
        )
    for title, japanese, reading, meaning, tags in VOCAB:
        upsert(
            f"vocab-{title.replace(' ', '-')}",
            item_type="vocabulary",
            title=title.title(),
            japanese=japanese,
            reading=reading,
            meaning=meaning,
            jlpt_level="N5",
            tags=tags,
        )
    for japanese, reading, meaning in KANJI:
        upsert(
            f"kanji-{japanese}",
            item_type="kanji",
            title=japanese,
            japanese=japanese,
            reading=reading,
            meaning=meaning,
            jlpt_level="N5",
            tags="kanji,n5",
        )
    for title, japanese, answer in CONJUGATIONS:
        upsert(
            f"conjugation-{title.split()[0]}-{answer}",
            item_type="conjugation",
            title=title,
            japanese=japanese,
            meaning=answer,
            explanation="Type the requested conjugated form.",
            tags="verbs,conjugation",
        )
    writing_items = [
        ("Write: I am a student.", "私は学生です。", "学生|です"),
        ("Write: I drank water yesterday.", "昨日水を飲みました。", "水|飲みました"),
        ("Write: I study Japanese every day.", "毎日日本語を勉強します。", "日本語|勉強"),
    ]
    for title, model, keywords in writing_items:
        upsert(f"writing-{title.lower().replace(':','').replace(' ','-')}", item_type="writing_prompt", title=title, japanese=model, meaning=keywords, tags="writing,n5")
    reading_item = upsert("reading-introductions", item_type="reading", title="Simple Introduction", japanese="私は学生です。日本語を勉強します。", meaning="I am a student. I study Japanese.", tags="reading,n5")
    if not ReadingPassage.query.filter_by(learning_item_id=reading_item.id).first():
        db.session.add(ReadingPassage(learning_item=reading_item, japanese_text=reading_item.japanese, furigana_text="わたしは がくせいです。にほんごを べんきょうします。", english_translation=reading_item.meaning, grammar_tags="state-of-being,particle-wo", vocabulary_tags="student,japanese"))
    listening_item = upsert("listening-greeting", item_type="listening", title="Greeting Clip", japanese="こんにちは。私は学生です。", meaning="Hello. I am a student.", tags="listening,n5")
    if not ListeningClip.query.filter_by(learning_item_id=listening_item.id).first():
        db.session.add(ListeningClip(learning_item=listening_item, audio_url="/static/audio/placeholder.mp3", transcript_japanese=listening_item.japanese, transcript_reading="こんにちは。わたしは がくせいです。", translation=listening_item.meaning))
    db.session.commit()


if __name__ == "__main__":
    with app.app_context():
        seed()
        print("Seed data loaded.")
