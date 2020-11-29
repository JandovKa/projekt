import json
# kokorinsko
kokorinsko_file = open('kokorinsko.json', encoding='utf-8')
text = kokorinsko_file.read()
kokorinsko_file.close()
raw_coordinates = json.loads(text)

formated_coordinates = []
for coordinate in raw_coordinates['features'][0]['geometry']['coordinates'][0]:
  formated_coordinates.append({ "lon": coordinate[0], "lat": coordinate[1] })

final = open('chko_kokorinsko_tableau.json', 'w', encoding='utf-8')
json.dump(formated_coordinates, final)
final.close()

#palava

palava_file = open('palava.json', encoding='utf-8')
text = palava_file.read()
palava_file.close()
raw_coordinates = json.loads(text)

formated_coordinates = []
for coordinate in raw_coordinates['features'][0]['geometry']['coordinates'][0]:
  formated_coordinates.append({ "lon": coordinate[0], "lat": coordinate[1] })

final = open('chko_palava_tableau.json', 'w', encoding='utf-8')
json.dump(formated_coordinates, final)
final.close()

#ceske stredohori
ceske_stredohori_file = open('ceske_stredohori.json', encoding='utf-8')
text = ceske_stredohori_file.read()
ceske_stredohori_file.close()
raw_coordinates = json.loads(text)

formated_coordinates = []
for coordinate in raw_coordinates['features'][0]['geometry']['coordinates'][0]:
  formated_coordinates.append({ "lon": coordinate[0], "lat": coordinate[1] })

final = open('chko_ceske_stredohori_tableau.json', 'w', encoding='utf-8')
json.dump(formated_coordinates, final)
final.close()

#labe
labe_file = open('elbe.json', encoding='utf-8')

text = labe_file.read()
labe_file.close()
raw_coordinates = json.loads(text)

coordinates_all = []
for seznam in raw_coordinates['features'][0]['geometry']['coordinates']:
  coordinates_all += seznam

formated_coordinates = []
for coordinate in coordinates_all:
  formated_coordinates.append({ "lon": coordinate[0], "lat": coordinate[1] })

final = open('labe_tableau.json', 'w', encoding='utf-8')
json.dump(formated_coordinates, final)
final.close()

