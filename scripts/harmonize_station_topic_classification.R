library(readr)
library(dplyr)
library(purrr)
library(stringr)

PROJ <- if (basename(getwd()) == "scripts") normalizePath("..") else normalizePath(".")
data_dir <- file.path(PROJ, "data")
od_dir <- file.path(data_dir, "od_subset")

topic_path <- file.path(data_dir, "station_topic_classification.csv")
lookup_path <- file.path(data_dir, "mrt_station_codes.csv")
output_path <- file.path(data_dir, "station_topic_classification_harmonized.csv")

topic_raw <- read_csv(
  topic_path,
  show_col_types = FALSE,
  col_types = cols(station_code = col_character())
)

topic_base <- topic_raw %>%
  mutate(station_code = as.character(station_code)) %>%
  arrange(desc(purity), desc(total_pois)) %>%
  distinct(station_code, .keep_all = TRUE)

lookup <- read_csv(
  lookup_path,
  show_col_types = FALSE,
  col_types = cols(stn_code = col_character())
)

od_files <- list.files(
  od_dir,
  pattern = "^origin_destination_train_.*\\.csv$",
  full.names = TRUE
)

compound_codes <- map_dfr(
  od_files,
  ~ read_csv(.x, show_col_types = FALSE, col_types = cols(
    ORIGIN_PT_CODE = col_character(),
    DESTINATION_PT_CODE = col_character()
  )) %>%
    {
      bind_rows(
        transmute(., code = ORIGIN_PT_CODE),
        transmute(., code = DESTINATION_PT_CODE)
      )
    }
) %>%
  distinct(code) %>%
  filter(str_detect(code, "/")) %>%
  pull(code)

compound_expansion <- map_dfr(compound_codes, function(compound_code) {
  parts <- str_split(compound_code, "/", simplify = TRUE)
  parts <- parts[parts != ""]

  station_names <- lookup %>%
    filter(stn_code %in% parts) %>%
    pull(station_name) %>%
    unique()

  # Only harmonize when all component codes resolve to the same physical station.
  if (length(station_names) != 1) {
    return(tibble())
  }

  alias_codes <- lookup %>%
    filter(station_name == station_names[[1]]) %>%
    pull(stn_code) %>%
    unique()

  source_row <- topic_base %>%
    filter(station_code %in% alias_codes) %>%
    arrange(desc(purity), desc(total_pois)) %>%
    slice_head(n = 1)

  if (nrow(source_row) == 0) {
    return(tibble())
  }

  tibble(
    station_name = station_names[[1]],
    source_station_code = source_row$station_code[[1]],
    target_station_code = unique(c(alias_codes, compound_code))
  ) %>%
    filter(!(target_station_code %in% topic_base$station_code)) %>%
    mutate(compound_code = compound_code)
})

new_rows <- compound_expansion %>%
  left_join(
    topic_base %>%
      rename(source_station_code = station_code),
    by = "source_station_code"
  ) %>%
  mutate(
    station_code = target_station_code,
    harmonized_from = source_station_code,
    harmonized_station_name = station_name
  ) %>%
  select(colnames(topic_base), harmonized_from, harmonized_station_name)

topic_harmonized <- topic_base %>%
  mutate(
    harmonized_from = NA_character_,
    harmonized_station_name = NA_character_
  ) %>%
  bind_rows(new_rows) %>%
  arrange(station_code, desc(purity), desc(total_pois)) %>%
  distinct(station_code, .keep_all = TRUE)

write_csv(topic_harmonized, output_path, na = "")

cat("Saved:", output_path, "\n")
cat("Original rows:", nrow(topic_base), "\n")
cat("Added rows:", nrow(new_rows), "\n")
cat("Final rows:", nrow(topic_harmonized), "\n")
