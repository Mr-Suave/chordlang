# Demo 4: Optimization Scope (Final)
# This version triggers Label Merging to reduce instruction count.

# 1. Math Folding (Runtime speedup, same instruction count)
tempo = 60 + 60
volume = 100 + 20

# 2. Nested Ifs (Structural cleanup - triggers _merge_labels)
# This creates multiple 'endif' labels at the exact same location.
# The optimizer will merge them, reducing the total instruction count.
if 1 > 0 then {
    if 2 > 1 then {
        if 3 > 2 then {
            play C4:500
        }
    }
}

# 3. Simple Play
play E4:500
