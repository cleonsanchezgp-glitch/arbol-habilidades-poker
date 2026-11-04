from pathlib import Path
from backend.storage import Store

store = Store(Path('.tmp-tsk017-data'))
document = store.list_documents()[0]
fragments = store.list_fragments(document['id'])
root = store.create_branch('Fundamentos')
second = store.create_branch('Postflop')
first = store.create_topic({
    'title': 'Posiciones de la mesa', 'summary': 'BTN y BB son posiciones.',
    'explanation': 'Contenido de prueba para la lectura.', 'difficulty': 'basic',
    'tags': ['posiciones'], 'examples': ['BTN actúa en posición.'],
})
later = store.create_topic({
    'title': 'Flop Axx', 'summary': 'Textura Axx de prueba.',
    'explanation': 'Contenido de prueba dependiente.', 'difficulty': 'intermediate',
})
store.link_evidence(first['id'], fragments[0]['id'])
store.link_evidence(later['id'], fragments[-1]['id'])
store.place_topic(first['id'], root['id'])
store.place_topic(later['id'], second['id'])
store.add_prerequisite(later['id'], first['id'])
with store.transaction() as db:
    db.execute('INSERT INTO topic_similarities(topic_id,candidate_id,score) VALUES (?,?,?)',
               (later['id'], first['id'], 0.71))
print(first['id'], later['id'])
