select distinct
    c.id                                                                                        as chantier_id,
    c.PES_Statut_Chantier__c                                                                    as chantier_statut,
    c.Date_de_la_commande_VT__c                                                                 as chantier_vt_date_commande,
    c.PES_Date_Visite_Technique__c                                                              as chantier_vt_date_realisation,
    LAST_VALUE(d.PES_Montant_TTC__c)
        OVER (PARTITION BY d.PES_Chantier__c ORDER BY d.createddate asc
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)                               as chantier_devis_montant
from DW_SALESFORCE_PES.pes_chantier as c
left join DW_SALESFORCE_PES.chantier_history_abandon_iso_chauffage as ab on ab.chantier_id = c.id
inner join DW_SALESFORCE_PES.pes_facture as f on f.PES_Chantier__c = c.id and f.PES_Statut__c = 'Soldée'
left join DW_SALESFORCE_PES.pes_paiement as p on p.Facture__c = f.id and p.PES_Mode_de_paiement__c != 'Avoir'
cross join DW_SALESFORCE_PES.temoin as t on t.Dossier__c = c.id
left join DW_SALESFORCE_PES.account as a
    on a.id = c.PES_Compte_associe__c
left join DW_SHERLOCK.opportunites as o on o.id = t.IdOpportuniteSherlock__c
join DW_SHERLOCK.solutions as s on o.solution_id = s.id
left join DW_VULCAIN.types_travaux as tt on s.vulcain_type_travaux_id = tt.id
left join chantier_isolation_devis_post_vt_envoye as devis_post_vt_envoye on devis_post_vt_envoye.PES_Chantier__c = c.id
left join chantier_isolation_devis_post_vt_signe as devis_post_vt_signe on devis_post_vt_signe.PES_Chantier__c = c.id
