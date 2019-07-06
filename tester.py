from distance_model import DistanceModel

model = DistanceModel("fruit", "apples")

while not model.iterate():
    pass

print(model.result)