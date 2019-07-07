from distance_model import DistanceModel

model = DistanceModel("Marco Polo", "Donald Trump")

while not model.iterate():
    pass

print(model.result)