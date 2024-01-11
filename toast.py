import numpy as np

untoasted_average = [176, 197, 219]
partial_average = [139,176,213]
toasted_average = [77, 92, 135]


average_colours = [untoasted_average, partial_average, toasted_average]
avg_split = []

for i in range(3):
	for j in range(3):
		avg_split.append(average_colours[i][j])

# print(avg_split)
crispinesses = [0,0.5,1]

crispinesses = np.vstack([crispinesses, np.ones(len(crispinesses))]).T

slope, intercept = np.linalg.lstsq(crispinesses, average_colours, rcond=None)[0]

def crispiness_to_colour(crispiness):
    return slope * crispiness + intercept

print(crispiness_to_colour(0))
# print(crispiness_to_colour(0.5))
# print(crispiness_to_colour(1))

# print(crispiness_to_colour(0.25))

# def expand_colour_range(colour, amount):
#     # expand a colour range by a certain amount
#     ranges = []
#     for i in range(3):
#         ranges.append([colour[i] - amount, colour[i] + amount])
#     return ranges