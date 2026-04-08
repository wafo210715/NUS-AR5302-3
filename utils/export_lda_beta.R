# Export beta (topic-word) matrices from R LDA models for coherence calculation
#
# This script loads the fitted LDA models and exports their beta matrices to CSV
# so that Python's gensim can calculate topic coherence scores.
#
# Usage: Rscript export_lda_beta.R

library(topicmodels)

# Paths
data_dir <- "data"
beta_dir <- file.path(data_dir, "lda_beta")
dir.create(beta_dir, showWarnings = FALSE, recursive = TRUE)

# K values
k_values <- c(4, 5, 6, 7, 8)

cat("Exporting LDA beta matrices...\n")

for (k in k_values) {
  cat(sprintf("  K=%d...", k))

  # Load model
  model_path <- file.path(data_dir, paste0("lda_model_k", k, ".rds"))

  if (!file.exists(model_path)) {
    cat(sprintf("  SKIP: Model not found: %s\n", model_path))
    next
  }

  model <- readRDS(model_path)

  # Extract beta matrix (topics x words)
  beta <- posterior(model)$terms

  # Export to CSV
  output_path <- file.path(beta_dir, paste0("beta_k", k, ".csv"))
  write.csv(beta, output_path, quote = FALSE)

  cat(sprintf("  Exported %s (%d topics x %d words)\n",
              output_path, nrow(beta), ncol(beta)))
}

cat("\nBeta matrices exported to:", beta_dir, "\n")
cat("Use calculate_topic_coherence_gensim.py to compute coherence scores.\n")
