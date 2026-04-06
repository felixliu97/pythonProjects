def countTrees(lines, right, down):
    trees, column = 0, 0
    for line in lines[::down]:
        width = len(line.strip())
        if line[column % width] == '#':
            trees += 1
        column += right
    return(trees)

with open('input-day3.txt', 'r') as f:
    lines = f.readlines()
    print(countTrees(lines,3,1))
    print(countTrees(lines,1,1) * countTrees(lines,3,1) * countTrees(lines,5,1) * countTrees(lines,7,1) * countTrees(lines,1,2))