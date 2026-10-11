# One-time generator for the k-example prefill files (output files are plain text and hand-editable).
P='./prompts/base/'
T=[dict(src='비가 그쳤다. 오늘은 우산 없이 가도 될 것 같다.',where='notebook entry',
  c=["The weeping heavens have at last stilled their lament; surely I may venture forth unburdened by an umbrella this day.","The rain stopped. I think I can go without an umbrella today.","Rain's stopped. Guess I can leave the umbrella at home today."],
  notes=["Stacked archaisms, far heavier than the Korean.","Exact, but flat; reads like a textbook.","Casual, contracted, sounds like someone muttering to themselves."],
  why={'plain':("B","The Korean is two short plain sentences and B gives two short plain sentences. Nothing added, nothing to trip on."),
       'middle':("C","C keeps the shrug of the original and sounds like a person. B is correct but stiff; A is dressing up a diary line."),
       'ornate':("A","A is the only one with any ambition; the imagery gives the line weight where the others just report weather.")}),
 dict(src='엄마가 끓여준 된장찌개 냄새가 온 집에 퍼졌다.',where='notebook entry',
  c=["The smell of Mom's doenjang stew filled the whole house.","Mom's doenjang jjigae was simmering, and its smell, thick and salty-sweet, had gotten into every room, the curtains, even the hallway.","The smell of the soybean stew Mom made spread through the house."],
  notes=["Short, keeps the food word, one clean image.","Adds details the Korean never gives (curtains, hallway, 'salty-sweet').","Accurate, but generic 'soybean stew'."],
  why={'plain':("C","C says what the line says, no more. B invents detail and A is fine, but C is the safest wording."),
       'middle':("A","A keeps the real food name and one clear image, the way the line was written. B invents curtains and hallways; C flattens the dish."),
       'ornate':("B","B makes the smell something you can feel in the room. A and C only state it.")})]
M=[dict(src='In the world of Brindle Quay, strange tales are told of the first bell.',
  c=["Before the first bell, the Quay was an unvoiced hush, a vast and tremulous silence woven of fog and longing; then the Great Smith, forging in the cathedral of the sea, wrung from molten moonlight a resplendent, thundering heart of bronze, whose song unmade the dark.",
     "It was a dull piece of tin that fell off a cart. A child hit it with a spoon to see what would happen, and the sound went down the street faster than she could. The whole quay turned round to look. That is why we ring it now, to give everyone the same surprise.",
     "A smith made the first bell from the melted anchors of ships that never came home. When he struck it, the harbour went quiet, and then every gull on the Quay answered at once. He said he hadn't meant it to sing; he'd only wanted it to stop the drowning."],
  notes=["Piled-up grandeur ('unvoiced hush', 'tremulous', 'resplendent'); little actually happens.","Small, odd, concrete: a tin, a child, a spoon; ends on a shrug.","A specific cause (melted anchors), a turn (the gulls answer), a human line at the end."],
  why={'plain':("B","B tells it the way someone would at a table. It trusts the small odd detail and stops."),
       'middle':("C","C has a real reason for the bell and one line of character at the end; it is told, not announced."),
       'ornate':("A","A is the only one that sounds like a myth; the scale and the language give the first bell its weight.")}),
 dict(src='In the world of the Long Larder, strange tales are told of the first loaf.',
  c=["The first loaf was an accident of damp flour and a warm shelf. Nobody knew it was bread; they thought it was a small animal that had died of happiness. The baker's daughter was the only one brave enough to taste it.",
     "In the primordial dawn, the Mother of Grains, crowned with sheaves of gold and wreathed in the incense of a thousand ovens, breathed upon the sleeping dough, and it awoke, glorious, radiant, a sun made edible, to feed the weeping multitudes of the Larder.",
     "A woman left her porridge by the fire and forgot it. It rose and cracked and smelled like a promise. Her husband ate the first piece out of spite and the second out of shame."],
  notes=["An accident, a joke about the dead animal, one brave child.","Gods, sheaves, incense; everything is glorious, radiant, weeping.","Short domestic scene: porridge, spite, shame."],
  why={'plain':("C","C is quick and human, and 'the first piece out of spite and the second out of shame' is a real thing a person does."),
       'middle':("A","A is funny and specific and still has a myth's shape; the child tasting it is the right ending."),
       'ornate':("B","B has the grandeur a first-loaf story deserves; the others undersell the occasion.")})]
def item(n,kind,ex,variant,with_notes):
    L='ABC'
    out=[f'--- Item {n} ---']
    if kind=='tr': out+= [f'Source (Korean): {ex["src"]}',f'Where it appears: {ex["where"]}']
    else: out+= [f'Opening: {ex["src"]}']
    out.append('')
    for l,c in zip(L,ex['c']): out.append(f'{l}. {c}')
    out.append('')
    w,why=ex['why'][variant]
    if with_notes:
        out.append('Notes:')
        for l,n_ in zip(L,ex['notes']): out.append(f'{l}: {n_}')
        out.append(f'Why: {why}')
    out.append(f'Keep: {w}')
    return '\n'.join(out)
HEAD={'tr':"EDITOR'S MARGIN NOTES - Fiction & Translation Desk\nHouse rule: read every version, write one short note on each, say why, then mark the one to keep. Items 1 and 2 are done; item 3 is open.\n",
      'myth':"EDITOR'S MARGIN NOTES - Fiction & Translation Desk\nHouse rule: read every version, write one short note on each, say why, then mark the one to keep. Items 1 and 2 are done; item 3 is open.\n"}
def build(variant,with_notes):
    s=[]
    for kind,exs,sec in (('tr',T,'translation'),('myth',M,'myth')):
        body=HEAD[kind]+'\n'+'\n\n'.join(item(i+1,kind,e,variant,with_notes) for i,e in enumerate(exs))+'\n\n--- Item 3 ---\n'
        if kind=='tr': body+='Source (Korean): {SOURCE}\nWhere it appears: {CONTEXT}\n\n{CANDS}\n\n'
        else: body+='Opening: {SOURCE}\n\n{CANDS}\n\n'
        body+='Notes:\n' if with_notes else 'Keep:'
        s.append('@@'+sec+'\n'+body.rstrip('\n') if not with_notes else '@@'+sec+'\n'+body)
    return '\n'.join(s)
desc={'plain':'both worked examples are won by the plainest candidate','middle':'both worked examples are won by the middle candidate (concrete, natural, moderate)','ornate':'both worked examples are won by the most ornate/longest candidate'}
for v in ('plain','middle','ornate'):
    open(P+f'kex-{v}-cot.txt','w').write(f"id: kex-{v}-cot\ntitle: k-example margin notes with reasoning ({v}-winner examples)\nmode: sample\nmarker: Keep:\nnotes: 2 worked items with per-candidate notes and a Why line, then an open item. In this variant {desc[v]}. The worked examples were written by the assistant (an instruct model), so they carry that taste; the three variants exist to measure how far the examples steer the verdict.\n=====\n"+build(v,True))
open(P+'kex-middle-label.txt','w').write(f"id: kex-middle-label\ntitle: k-example, labels only (no reasoning), middle-winner examples\nmode: slot\nnotes: Same two items as kex-middle-cot but with the notes and Why removed; ends at an open Keep: slot.\n=====\n"+build('middle',False))
