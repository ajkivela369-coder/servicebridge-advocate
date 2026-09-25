# R demonstrates research/statistical analysis around model evaluation.

labels <- c("PASS", "REVIEW", "FAIL", "PASS", "PASS", "REVIEW")
counts <- table(labels)
proportions <- prop.table(counts)

print(counts)
print(round(proportions, 3))

# Later: bootstrap confidence intervals and paired model comparisons belong here.
