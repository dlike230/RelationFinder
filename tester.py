from distance_model import DistanceModel

model = DistanceModel("fruit", "vegetable")

while not model.iterate():
    pass

print(model.result)