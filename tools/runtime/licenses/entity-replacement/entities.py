#!/usr/bin/env python3

"""entities.h generator"""

import re
import sys
import textwrap
from pathlib import Path

# get names for html-4.0 characters from:
#          https://html.spec.whatwg.org/entities.json
entity_name_length_max: int = 0
entity: dict[str, str] = {}
with open(Path(__file__).parent / "entities.html", "rb") as f:
    for rec in f:
        if m := re.match(
            rb'&lt;!ENTITY\s+(?P<name>[^\s]*)\s+CDATA\s+"&amp;#(?P<val>\d+);"\s+--', rec
        ):
            name = m.group("name").decode("utf-8")
            val = m.group("val").decode("utf-8")
            entity[name] = val
            entity_name_length_max = max(entity_name_length_max, len(name))

with open(sys.argv[1], "wt", encoding="utf-8") as f:
    f.write(
        textwrap.dedent(
            f"""\
    /*
     * Copyright © WHATWG (Apple, Google, Mozilla, Microsoft).
     * Copyright 1998 - 2011 W3C.
     * WHATWG portions incorporated into source code: BSD 3-Clause License.
     * Redistribution and use in source and binary forms, with or without
     * modification, are permitted provided that the following conditions are met:
     * 
     * 1. Redistributions of source code must retain the above copyright notice, this
     *    list of conditions and the following disclaimer.
     * 
     * 2. Redistributions in binary form must reproduce the above copyright notice,
     *    this list of conditions and the following disclaimer in the documentation
     *    and/or other materials provided with the distribution.
     * 
     * 3. Neither the name of the copyright holder nor the names of its
     *    contributors may be used to endorse or promote products derived from
     *    this software without specific prior written permission.
     * 
     * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
     * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
     * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
     * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
     * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
     * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
     * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
     * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
     * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
     * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
     * 
     * W3C selector portions: W3C Software and Document License 2002.
     * This work (and included software, documentation such as READMEs, or other related items) is being provided by the copyright holders under the following license.
     * License
     * By obtaining, using and/or copying this work, you (the licensee) agree that you have read, understood, and will comply with the following terms and conditions.
     * Permission to copy, modify, and distribute this software and its documentation, with or without modification, for any purpose and without fee or royalty is hereby granted, provided that you include the following on ALL copies of the software and documentation or portions thereof, including modifications:
     * The full text of this NOTICE in a location viewable to users of the redistributed or derivative work.
     * Any pre-existing intellectual property disclaimers, notices, or terms and conditions. If none exist, the W3C Software Short Notice should be included (hypertext is preferred, text is permitted) within the body of any redistributed or derivative code.
     * Notice of any changes or modifications to the files, including the date changes were made. (We recommend you provide URIs to the location from which the code is derived.)
     * Disclaimers
     * THIS SOFTWARE AND DOCUMENTATION IS PROVIDED "AS IS," AND COPYRIGHT HOLDERS MAKE NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO, WARRANTIES OF MERCHANTABILITY OR FITNESS FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF THE SOFTWARE OR DOCUMENTATION WILL NOT INFRINGE ANY THIRD PARTY PATENTS, COPYRIGHTS, TRADEMARKS OR OTHER RIGHTS.
     * COPYRIGHT HOLDERS WILL NOT BE LIABLE FOR ANY DIRECT, INDIRECT, SPECIAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF ANY USE OF THE SOFTWARE OR DOCUMENTATION.
     * The name and trademarks of copyright holders may NOT be used in advertising or publicity pertaining to the software without specific, written prior permission. Title to copyright in this software and any associated documentation will at all times remain with copyright holders.
     * 
     * Changes, 2026-10-28: select 252 names; preserve Graphviz legacy lang/rang values.
     * Data: https://html.spec.whatwg.org/entities.json
     * Selectors: https://www.w3.org/2003/entities/2007/xhtml1-{{lat1,special,symbol}}.ent
     */
    /// @file
    /// @ingroup common_utils
    /*
     * Generated file - do not edit directly.
     *
     * This file was generated from:
     *       https://html.spec.whatwg.org/entities.json
     * by means of the script:
     *       {Path(__file__).name}
     */

    #ifdef __cplusplus
    extern "C" {{
    #endif

    static const struct entities_s {{
    	char	*name;
    	int	value;
    }} entities[] = {{
    """
        )
    )
    for name, val in sorted(list(entity.items())):
        f.write(f'	{{"{name}", {val}}},\n')
    f.write(
        textwrap.dedent(
            f"""\
    }};

    #define ENTITY_NAME_LENGTH_MAX {entity_name_length_max}
    #define NR_OF_ENTITIES (sizeof(entities) / sizeof(entities[0]))

    #ifdef __cplusplus
    }}
    #endif
    """
        )
    )
