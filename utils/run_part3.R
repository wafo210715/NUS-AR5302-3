#!/usr/bin/env Rscript
# run_part3.R — Render Part 3 Rmd and export individual plots to docs/part3_plots/
# Run from the project root: Rscript run_part3.R

suppressPackageStartupMessages({
  library(rmarkdown)
  library(knitr)
  library(ggplot2)
})

proj_root <- normalizePath(".")
rmd_path  <- file.path(proj_root, "scripts", "part3_temporal_od_ari.Rmd")
out_dir   <- file.path(proj_root, "docs", "part3_plots")

dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

# ── 1. Render HTML report ─────────────────────────────────────────────────────
message("Rendering Rmd to HTML...")
rmarkdown::render(
  input      = rmd_path,
  output_dir = out_dir,
  quiet      = TRUE
)
message("  -> ", file.path(out_dir, "part3_temporal_od_ari.html"))

# ── 2. Re-source Rmd code and save individual plots ───────────────────────────
message("Exporting individual plots...")

r_script <- tempfile(fileext = ".R")
knitr::purl(rmd_path, output = r_script, quiet = TRUE)

env <- new.env(parent = globalenv())
source(r_script, local = env, echo = FALSE)

plots <- list(
  "01_monthly_volume"   = env$p_monthly,
  "02_heatmap"          = env$p_heatmap,
  "03_sem_vac"          = env$p_semvac,
  "04_intraday"         = env$p_intraday,
  "05_dest_function"    = env$p_dest,
  "06_dest_monthly_nus" = env$p_dest_monthly
)

# width x height in inches (match fig dimensions in Rmd chunks)
dims <- list(
  "01_monthly_volume"   = c(10, 5),
  "02_heatmap"          = c(10, 3.5),
  "03_sem_vac"          = c(10, 4.5),
  "04_intraday"         = c(10, 5.5),
  "05_dest_function"    = c(10, 5.5),
  "06_dest_monthly_nus" = c(10, 5)
)

for (nm in names(plots)) {
  out_path <- file.path(out_dir, paste0(nm, ".png"))
  ggsave(
    filename = out_path,
    plot     = plots[[nm]],
    width    = dims[[nm]][1],
    height   = dims[[nm]][2],
    dpi      = 150
  )
  message("  Saved: ", basename(out_path))
}

message("\nDone. All outputs in: ", out_dir)
