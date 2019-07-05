from distance_model import DistanceModel

model = DistanceModel("cherry", "apple")

while not model.iterate():
    pass

print(model.result)