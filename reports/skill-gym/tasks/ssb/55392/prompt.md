You are given a spreadsheet manipulation request from a real user,
plus three test-case workbooks: 1_input.xlsx, 2_input.xlsx, 3_input.xlsx
(same structure, different data).

Apply the request to EACH input workbook and save the results as
1_output.xlsx, 2_output.xlsx, 3_output.xlsx in the working directory.
Python with openpyxl is available at .venv/bin/python. Compute final VALUES
in the answer cells (formulas are also acceptable only if openpyxl would
show cached values; when in doubt, write computed values).

Do not modify the input files. Answers will be checked at position: 'Bank Balance'!AL4:AL21

<request>
In my Excel worksheet named 'Bank Balance', I have a cumulative formula in column AL that I want to stop calculating after the last entry, which is currently in row 21. Instead of stopping, the formula continues repeating the last value until the end of the worksheet. How can I adjust the formula so that it only calculates when there is a new entry and doesn't fill the rest of the column with the last value?
   My current formula is: IF(AND(AJ4="",AK4=""),"",AL3+AJ4-AK4) 
</request>
