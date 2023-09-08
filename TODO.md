# To-Do collection

## General
- [ ] Add example with more data
- [ ] Write diagrams which show how the structre and communication of the bw2extdb works 
- [ ] Implement parameter extraction (model, import, export)
- [ ] Update the class and method documentation
- [ ] Implement an automatic Documentation build
- [ ] Create a database migration structure see:  https://alembic.sqlalchemy.org/en/latest/tutorial.html and notes from Meeting with Geza
- [ ] Implement the case when the same database is uploaded several times to the database for shared working
- [ ] Write testing structure
- [ ] Add all data which does not match the schema in the catagories table to each Ex and Act


## Exporter
- [ ] go through the exporter and write out the extraction processes and all the underlying assumptions
- [ ] go through and implement the bullet points from the teams meetings: 20230612_SESAME_database_team_presentation
- [ ] check why the write `write_unlinked` method does not work
- [ ] write `check_datasetmetadata_completeness`
- [ ] implement versioning system in `create_version`

## Importer
- [ ] write `check_imported_data` if it makes sense
- [ ] check if the biosphere versions match

## Models
- [ ] rewrite the Read classes to not include the ID, except for activity_id
- [ ] Change that all exchnages and activities have the same variable name for activity_id
- [ ] Rethink if it makes sense to seperate technosphere and biosphere activities

## App
- [ ] On the importing routine, display what databases the imported database is dependent on?
- [ ] Change the user alternatives
