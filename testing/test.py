def my_function():
    x = 10
    local_vars = locals()
    local_vars['x'] = 20
    print(x)  # Still outputs: 10

my_function()