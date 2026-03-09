
#Checking figures 
annot <- read_csv("annot.csv", show_col_types = FALSE)
annot <- annot %>% 
        filter(topic %in% pol_issues) %>%
        dplyr::select(topic,semantic_validity_random)

annot$topic <- as.character(annot$topic)

irf_attentive <- irf_plot %>% 
                filter(cov == "attentive") %>% 
                mutate(val = case_when(
                  sign(lwr) == sign(upr) ~ pe, 
                  !(sign(lwr) == sign(upr)) ~ 0
                )) %>%
              dplyr::select(topic,val) %>%
              group_by(topic) %>%
              summarise(across(where(is.numeric), sum, na.rm = TRUE))

plot_irf <- left_join(annot, irf_attentive, by="topic") %>%
            arrange(semantic_validity_random)

png("data_prod/var/check/semantic_girfval.png", width = 800, height = 800)
p <- ggplot(plot_irf, aes(x=semantic_validity_random, y = val)) +
    geom_point(size = 3, fill='darkblue') + 
    geom_smooth(method = "lm")
print(p)
dev.off()

db <- read_csv("data_prod/var/general_TS.csv", show_col_types = FALSE)
throw_topic <-  c(13,21,22,23,29,40,43,44,52,53,57,65,70,73,75,76,89,94,96,117,0,1,2,3,4,14,17,25,28,35,37,50,51,54,63,67,68,69,71,74,77,79,80,82,83,86,87,90,98,104,105,106,112,116,59,38,110)
pol_issues <- setdiff(c(0:118), throw_topic)

db <- db %>%
  filter(topic %in% pol_issues)

db_size_top <- db %>% 
              dplyr::select(-date) %>%
              group_by(topic) %>%
              summarise(across(where(is.numeric), sum, na.rm = TRUE)) %>%
              ungroup() %>% 
              mutate(total = rowSums(across(-topic)))

db_size_top$topic = as.character(db_size_top$topic)
plot_irf <- left_join(db_size_top, irf_attentive, by="topic") %>%
            arrange(total)

png("data_prod/var/check/sizetop_girfval.png", width = 800, height = 800)
p <- ggplot(plot_irf, aes(x=total, y = val)) +
    geom_point(size = 3, fill='darkblue') + 
    geom_smooth(method = "lm")
print(p)
dev.off()

for (v in variables){
  db[[v]] <- log(db[[v]] + 1)
  db[[v]] <- scale(db[[v]], center=TRUE, scale=TRUE)[,1] 
}
db_long <- db %>%
          dplyr::select(all_of(variables)) %>%
          pivot_longer(cols = everything(), names_to = "variable", values_to = "valeur") %>%
          mutate(
            variable = recode(variable,
                         `lr` = "Députés LR",
                         `majority` = "Députés Ensemble",
                         `nupes` = "Députés NUPES",
                         `rn` ="Députés RN",
                         `lr_supp` = "Supporters LR",
                         `majority_supp` = "Supporters Ensemble",
                         `nupes_supp` =  "Supporters NUPES",
                         `rn_supp` =  "Supporters RN",
                         `attentive` = "Public Attentif",
                         `media` = "Média"
            ))

png("data_prod/var/check/groups_FDR.png", width = 1200, height = 1200)
p <- ggplot(db_long, aes(x = valeur, color=variable)) +
  stat_ecdf(size = .5) +
  scale_color_manual("", values = colors_dict) +
  labs(x = "Valeur", y = "Fonction de répartition F(x)", color = "Variable") +
  theme_minimal()
print(p)
dev.off()

#Figure 4 Barbera
plot_db <- irf_data  %>%
          mutate(
            cov = recode(cov,
                         `lr` = "Députés LR",
                         `majority` = "Députés Ensemble",
                         `nupes` = "Députés NUPES",
                         `rn` ="Députés RN",
                         `lr_supp` = "Supporters LR",
                         `majority_supp` = "Supporters Ensemble",
                         `nupes_supp` =   "Supporters NUPES",
                         `rn_supp` =  "Supporters RN",
                         `attentive` = "Public Attentif",
                         `media` = "Média"
            ),
            out = recode(out,
                         `lr` = "Députés LR",
                         `majority` = "Députés Ensemble",
                         `nupes` = "Députés NUPES",
                         `rn` ="Députés RN",
                         `lr_supp` = "Supporters LR",
                         `majority_supp` = "Supporters Ensemble",
                         `nupes_supp` =   "Supporters NUPES",
                         `rn_supp` =  "Supporters RN",
                         `attentive` = "Public Attentif",
                         `media` = "Média"
            )
          ) %>%
          mutate (
            cov = factor(cov, levels=readable_variables),
            out = factor(out, levels=readable_variables)
          ) %>%
          filter(cov_agenda_type != out_agenda_type | cov_agenda_type == "pol") %>%
          filter(sign(lwr) == sign(upr)) %>%
          group_by(topic, out) %>%
          slice_max(order_by = abs(pe), n = 2, with_ties = TRUE) %>%
          ungroup() %>%
          mutate(label = factor(label, levels = unique(label)))

colors_dict <- c(
  "Députés LR" = "blue",
  "Députés Ensemble" = "darkorange1",
  "Députés NUPES" = "red",
  "Députés RN" = "gray19",
  "Supporters LR" = "cyan3",
  "Supporters Ensemble" = "gold",
  "Supporters NUPES"= "orchid1",
  "Supporters RN" = "gray68",
  "Public Attentif"= "darkorchid3", 
  "Média" = "green4"
)


png("data_prod/var/irf-analysis/figure4.png", width = 1600, height = 1400)       
p <- ggplot(plot_db,
       aes(x = label, y = pe, ymin = lwr, ymax = upr)) +
  geom_pointrange(aes(col = cov), alpha = 0.4, size = 0.5) +
  geom_hline(yintercept = 0, color = "red") +
  facet_wrap(~out, nrow = 1) +
  coord_flip() +
  xlab("") +
  ylab(paste("\nThe effect of a standard error impulse", args$number_irf, "days ago by the covariate group, measured in std(Δresponse)")) +
  scale_color_manual("", values = colors_dict) +
  theme(
    panel.spacing = unit(1.25, "lines"),
    panel.background = element_blank(),
    panel.grid.major = element_line(colour = "gray90", linetype = "solid"),
    axis.text.x = element_text(size = 10, angle=45),
    axis.text.y = element_text(size = 16),
    strip.text = element_text(size = 10),
    panel.border = element_rect(colour = "black", fill = FALSE),
    strip.background = element_rect(colour = "black"),
    axis.title = element_text(size = 14),
    legend.text = element_text(size = 14, margin = margin(t = 20), vjust = 5)
  )
print(p)
dev.off()


#Start prepare aggregated figures
plot_db2 <- filt_irf %>%
          group_by(cov, out, cov_agenda_type, out_agenda_type) %>%
          summarise(
            lwr_sum = sum(lwr, na.rm = TRUE),
            pe_sum = sum(pe, na.rm = TRUE),
            upr_sum = sum(upr, na.rm = TRUE),
            .groups = "drop"
          )  %>%
          mutate(
            lwr_mean = lwr_sum / n_topic,
            pe_mean = pe_sum / n_topic, 
            upr_mean = upr_sum / n_topic
          ) %>%
          dplyr::select(-all_of(c("lwr_sum", "pe_sum", "upr_sum")))  %>%   
          mutate(
            cov = factor(cov, levels = readable_variables),
            out = factor(out, levels = readable_variables)
          )  %>%
          rename(
            lwr = lwr_mean,
            pe = pe_mean,
            upr = upr_mean
          ) 

#Figure : Influence entre députés 
plot_db <- plot_db2 %>%
            filter(cov_agenda_type == 'pol' & out_agenda_type=='pol')

plot_db$cov <- factor(plot_db$cov,
                      levels = rev(readable_variables[1:4]))
png("data_prod/var/irf-analysis/girf_between_deputes.png",width = 1000, height = 800)
p <- ggplot(plot_db,
       aes(x = cov, y = pe, ymin = lwr, ymax = upr)) +
  geom_segment(aes(x = cov, xend = cov, y = lwr, yend = upr), 
               size = 2.5) +
  facet_wrap(~ out, nrow = 1) +
  coord_flip() +
  xlab("") +
  scale_y_continuous(paste0("\n", args$number_irf,"-day Responses (in std(Δresponse)) of a one standard error shock of std(Δimpulse)"),
                     limits = c(0, 0.3), expand = c(0,0)) +
  theme(
    panel.spacing = unit(2, "lines"),
    legend.position = "bottom",
    panel.background = element_blank(),
    panel.grid.major = element_line(colour = "gray90", linetype = "solid"),
    axis.text = element_text(size = 15),
    axis.text.y = element_text(hjust=0),
    strip.text = element_text(size = 15),
    panel.border = element_rect(colour = "black", fill = FALSE),
    strip.background = element_rect(colour = "black"),
    axis.title = element_text(size = 16),
    legend.text = element_text(size = 16)
  )
print(p)
dev.off()    

#Figure 3 Barbera
plot_db <- plot_db2 %>%
            filter(cov_agenda_type != "media", out_agenda_type != "media") %>%
            filter(cov_agenda_type != out_agenda_type) %>%
            mutate(
              polgroup = ifelse(cov_agenda_type == "pol", as.character(cov), as.character(out)),
              pubgroup = ifelse(cov_agenda_type == "pub", as.character(cov), as.character(out)),
              var1 = cov,
              var2 = out,
              direction = ifelse(cov_agenda_type == "pol" & out_agenda_type == "pub", "députés→public", 
                                 ifelse(cov_agenda_type == "pub" & out_agenda_type == "pol", "public→députés", NA))
            ) %>%
            dplyr::select(polgroup, pubgroup, direction, pe, lwr, upr)%>%
              mutate(
                polgroup_f = factor(polgroup),
                polgroup_num = as.numeric(polgroup_f) + ifelse(direction == "députés→public", -0.15, 0.15)
              )


png("data_prod/var/irf-analysis/figure3.png",width = 1000, height = 1000)
p <- ggplot(plot_db,
       aes(x = polgroup_num, y = pe, ymin = lwr, ymax = upr, col = direction)) +
  geom_segment(aes(xend = polgroup_num, y = lwr, yend = upr),
               size = 4, alpha = 1) +  # retirer position_dodge ici
  geom_hline(yintercept = 0, color = "red") +
  facet_wrap(~ pubgroup, nrow = 1) +
  scale_x_continuous(
    name = "",
    breaks = unique(as.numeric(plot_db$polgroup_f)),
    labels = levels(plot_db$polgroup_f)
  ) +
  coord_flip() +
  ylab(paste0("\n", args$number_irf,"-day cumulative effect of one standard error shock in day 0")) +
  scale_color_manual("", values = c("gray70", "gray30")) +
  theme(
    panel.spacing = unit(1.1, "lines"),
    legend.position = "bottom",
    panel.background = element_blank(),
    panel.grid.major = element_line(colour = "gray90", linetype = "solid"),
    axis.text = element_text(size = 12),
    axis.text.x = element_text(size = 8, angle=45),
    strip.text = element_text(size = 12),
    panel.border = element_rect(colour = "black", fill = FALSE),
    strip.background = element_rect(fill = "gray80", color = "black"),
    axis.title = element_text(size = 16),
    legend.text = element_text(size = 16),
    axis.text.y = element_text(hjust=0),
    plot.margin = margin(t = 10, r = 40, b = 10, l = 10)  
  )

print(p)
dev.off()
#Figure 6 Barbera
plot_db <- plot_db2 %>%
          filter(cov_agenda_type == 'media' | out_agenda_type == 'media') %>%
          mutate(data_type = ifelse(cov_agenda_type == "media", "média→groupe", 
                                    ifelse(out_agenda_type == "media", "groupe→média", NA))) %>%
          mutate(y = ifelse(cov_agenda_type == 'media', as.character(out), as.character(cov)))


png("data_prod/var/irf-analysis/figure6.png",width = 800, height = 800)
p <- ggplot(plot_db,
       aes(x = y, y = pe, ymin = lwr, ymax = upr)) +
  geom_segment(aes(x = y, xend = y, y = lwr, yend = upr), 
               size = 4, alpha = 0.6) +
  #geom_segment(alpha = 0.8, size = 0.5) +
  geom_hline(yintercept = 0, color = "black") +
  facet_grid(~data_type) +
  coord_flip() +
  geom_vline(xintercept = 15) +
  xlab("") +
  scale_y_continuous(paste0("\nThe ", args$number_irf, "-day cumulative effect of a one standard error shock of std(Δimpulse) in day 0"),
                     expand = c(0,0.001)) +
  theme(
    panel.spacing = unit(1.5, "lines"),
    legend.position = "bottom",
    panel.background = element_blank(),
    panel.grid.major = element_line(colour = "gray90", linetype = "solid"),
    axis.text = element_text(size = 10),
    axis.text.y = element_text(hjust=0),
    strip.text = element_text(size = 16),
    panel.border = element_rect(colour = "black", fill = FALSE),
    strip.background = element_rect(colour = "black"),
    axis.title = element_text(size = 14),
    legend.text = element_text(size = 16)
  )
print(p)
dev.off()

#GIRF Figure 

matrix_LF <- filt_irf %>%
  group_by(cov, out) %>%
  summarise(pe_sum = round(sum(pe, na.rm = TRUE), 3), .groups = "drop") %>%
  complete(cov = readable_variables, out = readable_variables, fill = list(pe_sum = 0)) %>%
  mutate(
    cov = factor(cov, levels = readable_variables),
    out = factor(out, levels = readable_variables)
  )

png("data_prod/var/irf-analysis/total_GIRF_relations_pairs.png",width = 800, height = 600)
p <- ggplot(matrix_LF, aes(x = out, y = cov, fill = pe_sum)) +
  geom_tile(color = "white", linewidth = 0.3) +
  geom_text(aes(label = pe_sum), color = "black", size = 3) + 
  scale_fill_gradient(low = "#efffff", high = "#FF0000") +
  theme_minimal(base_size = 14) +
  labs(title = "Cumulative impulse by pair",
       x = "conséquence", y = "origine", fill = "Occurrences") +
  theme(axis.text.x = element_text(angle = 45, hjust = 1),
        panel.grid = element_blank(),
        plot.title = element_text(face = "bold", hjust = 0.5))
print(p)
dev.off()

#Tables 
#Top themes by LF pairs 
all_top3 <- data.frame(matrix(NA, nrow=0, ncol=5))
for(covar in readable_variables){
  for (outvar in readable_variables){
    if (covar == outvar){
      next
    }
    top3 <- filt_irf %>% 
      filter(cov == covar) %>%
      filter (out == outvar) %>%
      arrange(desc(abs(pe))) %>%              # Trier par pe décroissant
      dplyr::select(cov, out, pe, label) %>%    # Garder uniquement les colonnes voulues
      slice_head(n = 5) %>%
      mutate(rank=row_number())
    all_top3 <- rbind(all_top3, top3)
  }
}

colnames(all_top3) <- c("cov", "out", "pe", "label", "rank")

write.csv(all_top3, file="data_prod/var/irf-analysis/full_top5.csv", row.names=FALSE)

#Top 5 influences by topic
top3_topic <- filt_irf %>%
        group_by(topic, cov, label) %>%
        summarise(sum_pe = sum(pe, na.rm = TRUE),
      .groups='drop') %>%
    group_by(topic) %>%
    slice_max(order_by = sum_pe, n = 5, with_ties = FALSE)  %>% 
    ungroup()

print(paste("Dimensions : ", as.character(dim(top3_topic))))

top3_topic$rank <- rep(1:5, n_topic)

topics_leaders <- top3_topic %>%
      count(cov, rank) %>%
    tidyr::pivot_wider(
      names_from = cov,
      values_from = n,
      values_fill = 0  # remplit les NA par 0
    )

write.csv(topics_leaders, file="data_prod/var/irf-analysis/leader_bytopic_top5.csv", row.names=FALSE)

#Top 5 leading topics by group
top3_topics_group <- filt_irf %>%
          group_by(cov, topic, label) %>%
          summarise(sum_pe = sum(pe, na.rm= TRUE), .groups='drop') %>%
          group_by(cov) %>%
          slice_max(order_by = sum_pe, n = 5, with_ties = FALSE) %>%
          ungroup()

top3_topics_group$rank <- rep(1:5, length(variables))

groups_leaders <- top3_topics_group %>%
             dplyr::select(cov, rank, label) %>%
                tidyr::pivot_wider(
                  names_from = cov,
                  values_from = label
                )

write.csv(groups_leaders, file="data_prod/var/irf-analysis/topiclead_bygroup_top5.csv", row.names=FALSE)