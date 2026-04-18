library(tidyverse)
library(sf)
library(scales)
library(jsonlite)

theme_set(
  theme_minimal(base_size = 12) +
    theme(plot.title = element_text(face = "bold"))
)

univ_levels <- c("NUS", "NTU", "SMU", "SUTD")
univ_colors <- c(
  NUS  = "#8ECDB8",
  NTU  = "#4FA9C4",
  SMU  = "#F0C66B",
  SUTD = "#F28C4C"
)

proj_dir <- normalizePath("..")
data_dir <- file.path(proj_dir, "data")
od_dir <- file.path(data_dir, "od_subset")
scripts_figures_dir <- file.path(proj_dir, "scripts", "figures")
figures_dir <- file.path(proj_dir, "figures")

dir.create(scripts_figures_dir, showWarnings = FALSE, recursive = TRUE)
dir.create(figures_dir, showWarnings = FALSE, recursive = TRUE)

station_mapping <- read_csv(
  file.path(data_dir, "station_mapping.csv"),
  show_col_types = FALSE,
  col_types = cols(pt_code = col_character())
) %>%
  mutate(origin_university = factor(university, levels = univ_levels))

origin_lut <- station_mapping %>%
  transmute(
    ORIGIN_PT_CODE = pt_code,
    origin_university
  ) %>%
  distinct()

od_files <- list.files(od_dir, pattern = "\\.csv$", full.names = TRUE)

od_campus <- map_dfr(od_files, ~ read_csv(.x, show_col_types = FALSE)) %>%
  mutate(
    ORIGIN_PT_CODE = as.character(ORIGIN_PT_CODE),
    DESTINATION_PT_CODE = as.character(DESTINATION_PT_CODE)
  ) %>%
  inner_join(origin_lut, by = "ORIGIN_PT_CODE") %>%
  mutate(origin_university = factor(origin_university, levels = univ_levels))

bus_coords <- read_csv(
  file.path(data_dir, "sg_bus_stops_all.csv"),
  show_col_types = FALSE,
  col_types = cols(bus_stop_code = col_character())
) %>%
  transmute(pt_code = bus_stop_code, longitude, latitude)

mrt_coords <- read_csv(
  file.path(data_dir, "sg_mrt_stations_all.csv"),
  show_col_types = FALSE,
  col_types = cols(station_code = col_character())
) %>%
  transmute(pt_code = station_code, longitude, latitude)

all_coords <- bind_rows(bus_coords, mrt_coords) %>%
  filter(!is.na(longitude), !is.na(latitude)) %>%
  distinct(pt_code, .keep_all = TRUE)

sg_subzones <- st_read(
  file.path(data_dir, "MasterPlan2014SubzoneBoundaryWebSHP", "MP14_SUBZONE_WEB_PL.shp"),
  quiet = TRUE
) %>%
  st_transform(4326) %>%
  st_make_valid() %>%
  select(REGION_N)

sg_subzones_proj <- st_transform(sg_subzones, 3414)
sg_land <- st_union(sg_subzones_proj) %>%
  st_make_valid() %>%
  st_as_sf()
sg_bbox <- st_bbox(st_union(sg_subzones_proj) %>% st_make_valid())

campus_points <- station_mapping %>%
  group_by(origin_university) %>%
  summarise(
    campus_lon = mean(longitude, na.rm = TRUE),
    campus_lat = mean(latitude, na.rm = TRUE),
    .groups = "drop"
  )

destination_flow <- od_campus %>%
  left_join(all_coords, by = c("DESTINATION_PT_CODE" = "pt_code")) %>%
  filter(!is.na(longitude), !is.na(latitude)) %>%
  group_by(origin_university, DESTINATION_PT_CODE, longitude, latitude) %>%
  summarise(trips = sum(TOTAL_TRIPS), .groups = "drop") %>%
  left_join(campus_points, by = "origin_university") %>%
  mutate(
    line_alpha = rescale(log1p(trips), to = c(0.04, 0.25)),
    point_size = rescale(log1p(trips), to = c(0.45, 2.2))
  )

campus_points_sf <- campus_points %>%
  st_as_sf(coords = c("campus_lon", "campus_lat"), crs = 4326, remove = FALSE) %>%
  st_transform(3414)

destination_points_sf <- destination_flow %>%
  st_as_sf(coords = c("longitude", "latitude"), crs = 4326, remove = FALSE) %>%
  st_transform(3414)

campus_xy <- campus_points_sf %>%
  mutate(
    campus_x = st_coordinates(.)[, 1],
    campus_y = st_coordinates(.)[, 2]
  ) %>%
  st_drop_geometry()

destination_xy <- destination_points_sf %>%
  mutate(
    dest_x = st_coordinates(.)[, 1],
    dest_y = st_coordinates(.)[, 2]
  ) %>%
  st_drop_geometry() %>%
  left_join(campus_xy, by = "origin_university")

flow_lines_sf <- st_sf(
  destination_xy %>% select(origin_university, DESTINATION_PT_CODE, trips, line_alpha),
  geometry = st_sfc(
    pmap(
      list(destination_xy$campus_x, destination_xy$campus_y, destination_xy$dest_x, destination_xy$dest_y),
      function(campus_x, campus_y, dest_x, dest_y) {
        st_linestring(matrix(c(campus_x, dest_x, campus_y, dest_y), ncol = 2))
      }
    ),
    crs = 3414
  )
)

destination_point_xy <- destination_points_sf %>%
  mutate(
    dest_x = st_coordinates(.)[, 1],
    dest_y = st_coordinates(.)[, 2]
  ) %>%
  st_drop_geometry()

campus_label_xy <- campus_points_sf %>%
  mutate(
    label_x = st_coordinates(.)[, 1],
    label_y = st_coordinates(.)[, 2] + 1500
  ) %>%
  st_drop_geometry()

p_flow <- ggplot() +
  geom_sf(
    data = sg_subzones_proj,
    fill = "#FAFAFA",
    colour = "grey80",
    linewidth = 0.18
  ) +
  geom_sf(
    data = flow_lines_sf,
    aes(colour = origin_university, alpha = line_alpha),
    linewidth = 0.35,
    show.legend = c(alpha = FALSE)
  ) +
  geom_point(
    data = destination_point_xy,
    aes(
      x = dest_x,
      y = dest_y,
      colour = origin_university,
      size = point_size
    ),
    stroke = 0,
    alpha = 1,
    show.legend = c(size = FALSE)
  ) +
  geom_sf(
    data = campus_points_sf,
    aes(fill = origin_university),
    shape = 23,
    size = 4.2,
    colour = "#1A1A1A",
    stroke = 0.6
  ) +
  geom_text(
    data = campus_label_xy,
    aes(x = label_x, y = label_y, label = origin_university),
    colour = "#111111",
    size = 5.6,
    fontface = "bold",
    show.legend = FALSE
  ) +
  scale_colour_manual(values = univ_colors, name = "University") +
  scale_fill_manual(values = univ_colors, name = "University") +
  scale_alpha_identity() +
  scale_size_identity() +
  coord_sf(
    xlim = c(sg_bbox["xmin"], sg_bbox["xmax"]),
    ylim = c(sg_bbox["ymin"], sg_bbox["ymax"]),
    expand = FALSE
  ) +
  labs(
    title = "University-to-Destination Flow Distribution Across Singapore",
    subtitle = str_wrap("Distribution of trips from universities to destinations across Singapore.", width = 110),
    x = NULL,
    y = NULL
  ) +
  theme_minimal(base_size = 12) +
  theme(
    panel.grid.minor = element_blank(),
    panel.grid.major = element_line(colour = "grey90", linewidth = 0.3),
    legend.position = "bottom",
    legend.title = element_text(face = "bold"),
    plot.title = element_text(face = "bold"),
    plot.subtitle = element_text(colour = "grey30"),
    plot.caption = element_blank()
  )

scripts_output <- file.path(scripts_figures_dir, "destination_flow_map.png")
figures_output <- file.path(figures_dir, "part5_destination_flow_map.png")

ggsave(scripts_output, p_flow, width = 10.5, height = 8.5, dpi = 300)
ggsave(figures_output, p_flow, width = 10.5, height = 8.5, dpi = 300)

message("Saved flow map to: ", scripts_output)
message("Saved flow map to: ", figures_output)
