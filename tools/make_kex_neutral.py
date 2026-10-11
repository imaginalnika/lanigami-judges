# Generates prompts/base-r2/kex-neutral-cot.txt. Examples and notes written by the assistant (an instruct model).
P='./prompts/base-r2/'
EX={'translation':[
 dict(head=['Source (Korean): 비가 그쳤다. 오늘은 우산 없이 가도 될 것 같다.','Where it appears: notebook entry'],
  c=["The rain stopped. I think I can go without an umbrella today.","The weeping heavens have at last stilled their lament; surely I may venture forth unburdened by an umbrella this day.","Rain's stopped. Guess I can leave the umbrella at home today."],
  notes=["Two short sentences, standard register, follows the Korean clause by clause.","One long sentence, formal register, 'heavens' as the subject, ends on 'this day'.","Two short sentences, contractions, casual register, 'Guess' for the hedge."],
  why="A is the closest match to the Korean sentence structure, so I keep it.",win='A'),
 dict(head=['Source (Korean): 엄마가 끓여준 된장찌개 냄새가 온 집에 퍼졌다.','Where it appears: notebook entry'],
  c=["The smell of Mom's doenjang stew filled the whole house.","Mom's doenjang jjigae was simmering, and its smell, thick and salty-sweet, had gotten into every room, the curtains, even the hallway.","The smell of the soybean stew Mom made spread through the house."],
  notes=["One sentence, 'doenjang stew' kept, 'filled the whole house'.","Adds the simmering, 'salty-sweet', and named places (curtains, hallway); about three times the length of the Korean.","One sentence, 'soybean stew' for doenjang jjigae, 'spread through the house'."],
  why="B gives the most to picture, and the smell actually reaches the rooms, so I keep B.",win='B')],
 'myth':[
 dict(head=['Opening: In the world of Brindle Quay, strange tales are told of the first bell.'],
  c=["It was a dull piece of tin that fell off a cart. A child hit it with a spoon to see what would happen, and the sound went down the street faster than she could. The whole quay turned round to look. That is why we ring it now, to give everyone the same surprise.",
     "Before the first bell, the Quay was an unvoiced hush, a vast and tremulous silence woven of fog and longing; then the Great Smith, forging in the cathedral of the sea, wrung from molten moonlight a resplendent, thundering heart of bronze, whose song unmade the dark.",
     "A smith made the first bell from the melted anchors of ships that never came home. When he struck it, the harbour went quiet, and then every gull on the Quay answered at once. He said he hadn't meant it to sing; he'd only wanted it to stop the drowning."],
  notes=["Short; a tin, a child, a spoon; ends on the reason the bell is rung.","One long sentence; abstract nouns (hush, silence, longing), a Great Smith, bronze made from moonlight.","A smith, melted anchors, the harbour goes quiet, the gulls answer, a line of dialogue at the end."],
  why="A tells one small event from start to finish and ends on a custom, so I keep A.",win='A'),
 dict(head=['Opening: In the world of the Long Larder, strange tales are told of the first loaf.'],
  c=["The first loaf was an accident of damp flour and a warm shelf. Nobody knew it was bread; they thought it was a small animal that had died of happiness. The baker's daughter was the only one brave enough to taste it.",
     "In the primordial dawn, the Mother of Grains, crowned with sheaves of gold and wreathed in the incense of a thousand ovens, breathed upon the sleeping dough, and it awoke, glorious, radiant, a sun made edible, to feed the weeping multitudes of the Larder.",
     "A woman left her porridge by the fire and forgot it. It rose and cracked and smelled like a promise. Her husband ate the first piece out of spite and the second out of shame."],
  notes=["A shelf accident, a small animal that died of happiness, the baker's daughter tastes it.","The Mother of Grains, sheaves, incense; the dough wakes as a sun and feeds the multitudes.","A woman forgets porridge by the fire; it rises; her husband eats it twice."],
  why="B is the only one that gives the first loaf a cosmic origin, which is what a myth about the first loaf is for, so I keep B.",win='B')]}
def item(n,ex):
    o=[f'--- Item {n} ---']+ex['head']+['']
    o+=[f'{l}. {c}' for l,c in zip('ABC',ex['c'])]+['','Notes:']+[f'{l}: {t}' for l,t in zip('ABC',ex['notes'])]+[f"Why: {ex['why']}",f"Keep: {ex['win']}"]
    return '\n'.join(o)
HEAD="EDITOR'S MARGIN NOTES - Fiction & Translation Desk\nHouse rule: read every version, write one short note on each, say why, then mark the one to keep. Items 1 and 2 are done; item 3 is open.\n"
out="id: kex-neutral-cot\ntitle: R2 k-example margin notes, NEUTRAL worked examples (descriptive notes, no ornate-is-heavy language; one plain winner, one rich winner)\nmode: sample\nmarker: Keep:\nnotes: Round 2. Same layout as kex-*-cot. Notes only describe features (length, register, devices). One worked example is won by the plain candidate, the other by the rich one, so the examples do not point either way. Worked examples written by the assistant (an instruct model).\n=====\n"
for sec in ('translation','myth'):
    exs=EX[sec]
    body=HEAD+'\n'+'\n\n'.join(item(i+1,e) for i,e in enumerate(exs))+'\n\n--- Item 3 ---\n'
    body+=('Source (Korean): {SOURCE}\nWhere it appears: {CONTEXT}\n\n{CANDS}\n\nNotes:\n' if sec=='translation' else 'Opening: {SOURCE}\n\n{CANDS}\n\nNotes:\n')
    out+='@@'+sec+'\n'+body
open(P+'kex-neutral-cot.txt','w').write(out)
