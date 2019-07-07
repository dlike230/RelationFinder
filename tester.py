from distance_model import DistanceModel

model = DistanceModel("fruit", "schizocarp")

while not model.iterate():
    pass

print(model.result)