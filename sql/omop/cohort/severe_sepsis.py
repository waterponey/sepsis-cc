--3912 occurrences
SELECT c.concept_name, COUNT(*)
FROM condition_occurrence co, visit_occurrence vo, concept c 
where 
co.condition_source_concept_id = c.concept_id
and co.visit_occurrence_id = vo.visit_occurrence_id
and lower(c.concept_name) like lower('%sepsis%')
group by c.concept_name  ORDER BY count(1) desc 
limit 1000
