# Git-Diff SQL-Changes

A simple project, the purpose of which is to obtain information about changes in SQL files in Git Repos.



## Supported changes

 * __Whitespace__ - Category of changes related to blank lines, spaces, etc.
 * __DML__ - Changes in DML (Data Manipulation Language)
 * __Index__ - Index Changes
 * __Comments__ - Changes associated with single-line or multi-line comments
 * __NoDiffInfo__ - Lack of information about changes
 * __Privilege__ - Privilege Changes
 * __PK__ - Primary Key Changes
 * __Engine__ - Changes related to storage engines (e.g., MyISAM -> InnoDB)
 * __Renaming__ - Determining the renamed files (with or without change of content)


## TODOs

 * Reduce False Positives
 * Add other categories: Foreign Keys, Typos, Type Changes, etc.

