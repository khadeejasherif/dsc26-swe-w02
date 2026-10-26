# AI usage

Keep all three headings exactly as they are. If this file is missing or any heading is
missing, the grader stops and gives 0 ("AI_USAGE.md missing or incomplete"). The content
is not scored, but your Track Mentor reads it and the W8 defence can ask about it.

## Tools

<!-- Which tools you used (ChatGPT, Copilot, Claude, Cursor, none...) and for which parts. -->
-chatgpt

## What AI got wrong

<!-- At least one thing an assistant got wrong that you changed, and how you noticed
(a test failed, the docs said otherwise, you ran it). -->
I asked ai to help me in the get parcels with limit and it done a function with offset 
which it's not efficient so i updated some of it to match cursor logic

## In my own words

<!-- Answer without AI, one or two sentences each. -->

1. Why does `listParcels` need a cursor rather than an offset?

As with offset if I added parcels while getting he parcels the offset can skip parcels , while on curser i save the value of the element after last element (next cursor()) to so when it's renderng the next 10 elements it will begin from the last element without skipping any elements in case of updating parcels

2. Which of your four operations would break the courier app if you renamed one field, and who would have to approve that change?

i think the 4 will break, and i would ask the contract owner or lead.
