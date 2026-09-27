-- Sample Fixture Queries for Testing
SELECT * FROM `bigquery-public-data.usa_names.usa_1910_current`;
SELECT * FROM `bigquery-public-data.usa_names.usa_1910_current` LIMIT 5;
SELECT name, number FROM `bigquery-public-data.usa_names.usa_1910_current` WHERE state = 'NY';
