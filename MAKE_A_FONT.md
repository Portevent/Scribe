
## Drawing an Inkscape font

1. Draw each letter as a path (convert shapes and strokes with *Path > Object to Path*). A letter
   made of several paths can be grouped.
2. Give each path or group a label equal to its character. Several objects with the same label
   become variants.
3. Put letters that share a baseline on the same row; descenders (`g`, `p`, `y`…) may go below it.
4. Only translations and scales are supported as transforms (no rotation or skew).
5. Check the result with `inspect_font.py`.

The space between letters is computed from the row height; it can be adjusted with
`--letter-spacing`.
