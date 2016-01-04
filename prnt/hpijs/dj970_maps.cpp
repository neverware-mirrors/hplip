/*****************************************************************************\
  dj970_maps.cpp : Color maps for DJ970

  Copyright (c) 1996 - 2001UL, Hewlett-Packard Co.
  All rights reserved.

  Redistribution and use in source and binary forms, with or without
  modification, are permitted provided that the following conditions
  are met:
  1. Redistributions of source code must retain the above copyright
     notice, this list of conditions and the following disclaimer.
  2. Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.
  3. Neither the name of Hewlett-Packard nor the names of its
     contributors may be used to endorse or promote products derived
     from this software without specific prior written permission.

  THIS SOFTWARE IS PROVIDED BY THE AUTHOR "AS IS" AND ANY EXPRESS OR IMPLIED
  WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
  MERCHANTABILITY AND FITNESS FOR A PARTICAR PURPOSE ARE DISCLAIMED.  IN
  NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
  TO, PATENT INFRINGEMENT; PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
  OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
  ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
  THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
\*****************************************************************************/


#include "config.h"

#include "global_types.h"

APDK_BEGIN_NAMESPACE

#if defined(APDK_DJ9xx)

// 600x600x1, K    - Plain, Normal, Grey

uint32_t ulMapGRAY_K_6x6x1[] =
{
    255UL, 238UL, 218UL, 204UL, 189UL, 181UL, 171UL, 161UL, 154UL,
    178UL, 168UL, 161UL, 153UL, 148UL, 141UL, 136UL, 130UL, 127UL,
    140UL, 133UL, 129UL, 124UL, 121UL, 116UL, 113UL, 109UL, 106UL,
    115UL, 112UL, 108UL, 104UL, 101UL,  97UL,  95UL,  91UL,  89UL,
     96UL,  94UL,  90UL,  88UL,  85UL,  82UL,  79UL,  77UL,  74UL,
     81UL,  78UL,  76UL,  73UL,  71UL,  69UL,  66UL,  65UL,  62UL,
     67UL,  66UL,  63UL,  62UL,  59UL,  57UL,  55UL,  54UL,  51UL,
     56UL,  55UL,  52UL,  51UL,  49UL,  47UL,  45UL,  44UL,  42UL,
     47UL,  45UL,  43UL,  41UL,  40UL,  38UL,  37UL,  35UL,  33UL,
    209UL, 191UL, 184UL, 173UL, 166UL, 156UL, 151UL, 144UL, 140UL,
    154UL, 149UL, 143UL, 138UL, 132UL, 128UL, 123UL, 120UL, 115UL,
    127UL, 122UL, 119UL, 114UL, 111UL, 107UL, 104UL, 100UL,  96UL,
    106UL, 102UL,  99UL,  95UL,  93UL,  90UL,  87UL,  84UL,  81UL,
     89UL,  85UL,  83UL,  80UL,  78UL,  75UL,  73UL,  70UL,  68UL,
     74UL,  71UL,  69UL,  67UL,  65UL,  63UL,  61UL,  59UL,  57UL,
     62UL,  60UL,  58UL,  56UL,  54UL,  52UL,  50UL,  48UL,  47UL,
     51UL,  50UL,  48UL,  46UL,  44UL,  43UL,  41UL,  39UL,  38UL,
     42UL,  40UL,  38UL,  37UL,  35UL,  34UL,  32UL,  31UL,  29UL,
    176UL, 168UL, 159UL, 153UL, 146UL, 141UL, 135UL, 130UL, 125UL,
    140UL, 133UL, 129UL, 124UL, 121UL, 116UL, 113UL, 109UL, 106UL,
    115UL, 112UL, 108UL, 104UL, 101UL,  97UL,  95UL,  91UL,  89UL,
     96UL,  94UL,  90UL,  88UL,  85UL,  82UL,  79UL,  77UL,  74UL,
     81UL,  78UL,  76UL,  73UL,  71UL,  69UL,  66UL,  65UL,  62UL,
     67UL,  66UL,  63UL,  62UL,  59UL,  57UL,  55UL,  54UL,  51UL,
     56UL,  55UL,  52UL,  51UL,  49UL,  47UL,  45UL,  44UL,  42UL,
     47UL,  45UL,  43UL,  41UL,  40UL,  38UL,  37UL,  35UL,  33UL,
     38UL,  36UL,  34UL,  32UL,  31UL,  29UL,  28UL,  26UL,  25UL,
    153UL, 148UL, 143UL, 136UL, 132UL, 127UL, 122UL, 119UL, 114UL,
    125UL, 122UL, 118UL, 114UL, 110UL, 107UL, 103UL, 100UL,  96UL,
    105UL, 102UL,  98UL,  95UL,  92UL,  90UL,  86UL,  84UL,  81UL,
     88UL,  85UL,  83UL,  80UL,  77UL,  75UL,  72UL,  70UL,  67UL,
     74UL,  71UL,  69UL,  67UL,  65UL,  63UL,  61UL,  59UL,  57UL,
     62UL,  60UL,  58UL,  56UL,  54UL,  52UL,  50UL,  48UL,  47UL,
     51UL,  49UL,  48UL,  46UL,  44UL,  42UL,  41UL,  39UL,  38UL,
     42UL,  40UL,  38UL,  37UL,  35UL,  33UL,  32UL,  30UL,  29UL,
     33UL,  31UL,  30UL,  28UL,  27UL,  25UL,  24UL,  22UL,  21UL,
    138UL, 132UL, 128UL, 123UL, 120UL, 115UL, 112UL, 108UL, 105UL,
    115UL, 111UL, 108UL, 104UL, 101UL,  97UL,  95UL,  91UL,  89UL,
     96UL,  93UL,  90UL,  87UL,  85UL,  81UL,  79UL,  76UL,  74UL,
     81UL,  78UL,  76UL,  73UL,  71UL,  68UL,  66UL,  64UL,  62UL,
     67UL,  66UL,  63UL,  62UL,  59UL,  57UL,  55UL,  53UL,  51UL,
     56UL,  55UL,  52UL,  51UL,  49UL,  47UL,  45UL,  44UL,  42UL,
     46UL,  45UL,  43UL,  41UL,  39UL,  38UL,  36UL,  35UL,  33UL,
     37UL,  36UL,  34UL,  32UL,  31UL,  29UL,  28UL,  26UL,  25UL,
     28UL,  27UL,  26UL,  24UL,  22UL,  21UL,  19UL,  18UL,  16UL,
    124UL, 121UL, 116UL, 113UL, 109UL, 106UL, 102UL,  99UL,  95UL,
    105UL, 102UL,  98UL,  95UL,  92UL,  90UL,  86UL,  83UL,  81UL,
     88UL,  85UL,  82UL,  80UL,  77UL,  75UL,  72UL,  70UL,  67UL,
     73UL,  71UL,  69UL,  67UL,  65UL,  63UL,  60UL,  59UL,  56UL,
     62UL,  60UL,  57UL,  56UL,  54UL,  52UL,  50UL,  48UL,  46UL,
     51UL,  49UL,  48UL,  46UL,  44UL,  42UL,  40UL,  39UL,  37UL,
     42UL,  40UL,  38UL,  37UL,  35UL,  33UL,  32UL,  30UL,  29UL,
     33UL,  31UL,  30UL,  28UL,  27UL,  25UL,  24UL,  22UL,  21UL,
     25UL,  23UL,  22UL,  20UL,  19UL,  17UL,  16UL,  14UL,  12UL,
    114UL, 110UL, 107UL, 103UL, 100UL,  96UL,  94UL,  90UL,  88UL,
     95UL,  93UL,  90UL,  87UL,  84UL,  81UL,  78UL,  76UL,  73UL,
     81UL,  78UL,  76UL,  73UL,  71UL,  68UL,  66UL,  64UL,  62UL,
     67UL,  65UL,  63UL,  61UL,  59UL,  57UL,  55UL,  53UL,  51UL,
     56UL,  54UL,  52UL,  50UL,  49UL,  47UL,  45UL,  43UL,  42UL,
     46UL,  44UL,  43UL,  41UL,  39UL,  38UL,  36UL,  34UL,  33UL,
     37UL,  36UL,  34UL,  32UL,  31UL,  29UL,  28UL,  26UL,  25UL,
     28UL,  27UL,  25UL,  24UL,  22UL,  21UL,  19UL,  18UL,  16UL,
     20UL,  19UL,  17UL,  16UL,  14UL,  13UL,  11UL,  10UL,   8UL,
    104UL, 101UL,  97UL,  95UL,  91UL,  89UL,  85UL,  83UL,  80UL,
     88UL,  85UL,  82UL,  79UL,  77UL,  74UL,  72UL,  69UL,  67UL,
     73UL,  71UL,  69UL,  66UL,  65UL,  62UL,  60UL,  58UL,  56UL,
     62UL,  60UL,  57UL,  56UL,  54UL,  52UL,  50UL,  48UL,  46UL,
     51UL,  49UL,  47UL,  46UL,  44UL,  42UL,  40UL,  39UL,  37UL,
     41UL,  40UL,  38UL,  37UL,  35UL,  33UL,  31UL,  30UL,  28UL,
     32UL,  31UL,  29UL,  28UL,  26UL,  25UL,  23UL,  22UL,  20UL,
     25UL,  23UL,  22UL,  20UL,  19UL,  17UL,  16UL,  14UL,  12UL,
     16UL,  15UL,  13UL,  12UL,  10UL,   9UL,   7UL,   6UL,   4UL,
     95UL,  92UL,  90UL,  86UL,  84UL,  81UL,  78UL,  76UL,  73UL,
     80UL,  78UL,  75UL,  73UL,  70UL,  68UL,  66UL,  64UL,  62UL,
     67UL,  65UL,  63UL,  61UL,  59UL,  57UL,  55UL,  53UL,  51UL,
     56UL,  54UL,  52UL,  50UL,  48UL,  47UL,  45UL,  43UL,  41UL,
     46UL,  44UL,  43UL,  41UL,  39UL,  38UL,  36UL,  34UL,  33UL,
     37UL,  35UL,  34UL,  32UL,  31UL,  29UL,  28UL,  26UL,  25UL,
     28UL,  27UL,  25UL,  24UL,  22UL,  21UL,  19UL,  18UL,  16UL,
     20UL,  19UL,  17UL,  16UL,  14UL,  12UL,  11UL,   9UL,   8UL,
     12UL,  11UL,   9UL,   8UL,   6UL,   5UL,   3UL,   2UL,   0UL
};
#endif

uint32_t ulMapBROADWAY_KCMY[ 9*9*9 ]=
{
 673723135UL,   26007371UL,    9756717UL,   10020638UL,   10022677UL,   10153743UL, 
  10285066UL,   10416133UL,    9169408UL, 3405886809UL,      59743UL,   23980849UL, 
   9366812UL,   10153744UL,   10285066UL,   10153990UL,   10087424UL,    9169408UL, 
3858807091UL, 2197868343UL,      60220UL,    4714015UL,    7270155UL,    8646656UL, 
   8579328UL,    8382208UL,    7791360UL, 3875584801UL, 3187785766UL, 1660999718UL, 
     60710UL,   36498447UL,    4646144UL,    5166848UL,    5624832UL,    5886976UL, 
3875585303UL, 3573661210UL, 2667629594UL, 1208016666UL,  319808529UL,  304931585UL, 
   3000832UL,    3652608UL,    4176384UL, 3892820492UL, 3758145040UL, 3187721745UL, 
2197869329UL,  939582223UL,  387244805UL,  152818688UL,    2341120UL,    2927872UL, 
3909859588UL, 3892624647UL, 3472998923UL, 2835401737UL, 1728109064UL,  957341698UL, 
 336716032UL,    1099008UL,    1944832UL, 3909661952UL, 3909269763UL, 3741368579UL, 
3238053891UL, 2516635904UL, 1375786499UL,  688380160UL,      56064UL,    1031168UL, 
3925912832UL, 3909136896UL, 3691033856UL, 3355490816UL, 2717957120UL, 1778432512UL, 
 973126144UL,  436259072UL,      54784UL, 3183805035UL,   13972558UL,   11965228UL, 
  11449373UL,   10995222UL,   27643922UL,   27514893UL,   27451400UL,    9560832UL, 
4015155266UL, 1835890539UL,  211079218UL,   26991389UL,   27255056UL,   27321354UL, 
  10087171UL,    9168128UL,    8249088UL, 3928464674UL, 3004413502UL,  809093171UL, 
 308797461UL,  109046276UL,    8512768UL,    8118528UL,    7658752UL,    7133184UL, 
3910708498UL, 3523329062UL, 2165818909UL,  993775120UL,  575525632UL,    4378368UL, 
   5164288UL,    5623040UL,    5753856UL, 3910513160UL, 3892624145UL, 2919613972UL, 
1730004745UL,  892520192UL,  288014592UL,    2864640UL,    3649536UL,    4240640UL, 
3910120707UL, 3892689928UL, 3305161995UL, 2349777670UL, 1276887296UL,  505330688UL, 
 119058688UL,    2204416UL,    2859264UL, 3909923840UL, 3909138435UL, 3523263488UL, 
2802367488UL, 1661777152UL,  823047168UL,  252687104UL,     958464UL,    1873408UL, 
3925912576UL, 3691030016UL, 3338708224UL, 2801837312UL, 1912644608UL, 1057007104UL, 
 520136448UL,   84257792UL,     956928UL, 3724581888UL, 3506475520UL, 3254817536UL, 
2852164608UL, 2214631936UL, 1493213184UL,  855680256UL,  385919744UL,      44544UL, 
3805020222UL,  904134721UL,   14429742UL,   12876059UL,   12034579UL,   11580943UL, 
  11387914UL,   11128584UL,   10082048UL, 3935974696UL, 2377526339UL,  381966891UL, 
  12422935UL,   11841035UL,   11517956UL,   10734848UL,    9752576UL,    8441856UL, 
4017191173UL, 3663951909UL, 2509611275UL, 1100725504UL,  226741760UL,    7917824UL, 
   7590144UL,    7129856UL,    6668800UL, 3980299776UL, 3895762190UL, 3075845379UL, 
1583263232UL,  559065856UL,    4698880UL,    5421824UL,    5684224UL,    5618176UL, 
3961691136UL, 3927877891UL, 3375083778UL, 1932502272UL,  875864832UL,  271360256UL, 
   3056128UL,    3909376UL,    4369408UL, 3943867136UL, 3926765056UL, 3474239744UL, 
2300093184UL, 1176083200UL,  538810368UL,  102274048UL,    2199808UL,    2921984UL, 
3943081472UL, 3791692800UL, 3305152000UL, 2433193984UL, 1443467776UL,  738889472UL, 
 286100736UL,     886016UL,    1737216UL, 3875577088UL, 3439363584UL, 3120596736UL, 
2516616704UL, 1660978688UL,  973113088UL,  453019136UL,      33280UL,     883456UL, 
3573581056UL, 3271587328UL, 2986374144UL, 2499834880UL, 1862301440UL, 1291876864UL, 
 805339648UL,  352355328UL,      33792UL, 3838771235UL, 2229010470UL,  233504809UL, 
  14755610UL,   13525519UL,   12553738UL,   12035848UL,   11647238UL,   10798848UL, 
3904054036UL, 3200782122UL, 1003559969UL,  131218706UL,   13266692UL,   12162304UL, 
  11511808UL,   10859264UL,   10009088UL, 4002237696UL, 3801629204UL, 2762892800UL, 
1152083712UL,  194999040UL,    9931776UL,    9608448UL,    8889856UL,    7842560UL, 
4098708736UL, 3999230464UL, 3127209220UL, 1583244288UL,  609975040UL,    5149696UL, 
   5547520UL,    5679872UL,    5548032UL, 4062537728UL, 3978851584UL, 3106761472UL, 
1882548992UL,  926511360UL,  288454400UL,    3375616UL,    4101120UL,    4364800UL, 
4027612672UL, 3943597056UL, 3222631168UL, 2132504320UL, 1159557120UL,  538996992UL, 
 102461696UL,    2389760UL,    2982400UL, 3942679808UL, 3707795968UL, 3120589824UL, 
2315808768UL, 1393257984UL,  722234368UL,  286157568UL,     944384UL,    1797120UL, 
3741350656UL, 3321914624UL, 2952815360UL, 2365613824UL, 1543530240UL,  922772736UL, 
 436233472UL,      24832UL,     812032UL, 3472911104UL, 3137363200UL, 2785040896UL, 
2281724672UL, 1660967680UL, 1157651968UL,  738222592UL,  335569664UL,      25088UL, 
3838836756UL, 2899836951UL, 1189412888UL,   15597591UL,   15015690UL,   13914373UL, 
  13007875UL,   12360194UL,   11578624UL, 3904642310UL, 3503097879UL, 1725237778UL, 
 601694217UL,   81081089UL,   12932864UL,   12089088UL,   11308032UL,   10787840UL, 
3969395712UL, 3853397762UL, 2779723008UL, 1269511680UL,  346766080UL,   10637312UL, 
  10185984UL,    9666560UL,    8948992UL, 4099617792UL, 3882433280UL, 2875668992UL, 
1617574912UL,  661537024UL,    6703360UL,    7300096UL,    7436032UL,    6914048UL, 
4163778304UL, 3945872896UL, 3107536896UL, 1966948864UL, 1061110784UL,  322653952UL, 
   3824896UL,    4420096UL,    4553728UL, 4128524288UL, 3977595904UL, 3122152448UL, 
2082292736UL, 1176585984UL,  589516032UL,  102715136UL,    2579200UL,    3172608UL, 
4110440960UL, 3674230016UL, 3037153536UL, 2181711872UL, 1376668672UL,  739200512UL, 
 269504512UL,    1134336UL,    1922048UL, 3741342208UL, 3254799360UL, 2835367936UL, 
2197833216UL, 1442859008UL,  889211648UL,  419449600UL,      18688UL,     806144UL, 
3422573824UL, 3019917824UL, 2650817792UL, 2113946880UL, 1560299264UL, 1107315200UL, 
 721439488UL,  352341248UL,      18944UL, 3855353864UL, 3235184653UL, 2011168781UL, 
 585826314UL,   15468551UL,   15145472UL,   14304000UL,   13461760UL,   12749312UL, 
3904640001UL, 3671001096UL, 2463697669UL,  936907522UL,  232003840UL,   13181952UL, 
  12534272UL,   11886336UL,   11237120UL, 3969652992UL, 3853391872UL, 2846693888UL, 
1353390848UL,  481238528UL,   11084800UL,   10895616UL,   10377216UL,    9660928UL, 
4083424768UL, 3815579136UL, 2825527296UL, 1634542080UL,  779232256UL,  158607360UL, 
   7945472UL,    8147200UL,    7757824UL, 4164428544UL, 3694667008UL, 2822513920UL, 
1849763328UL,  994387968UL,  340339456UL,    4929536UL,    5655808UL,    5724672UL, 
4212793856UL, 3894158848UL, 3072403712UL, 2082810624UL, 1227304192UL,  656878080UL, 
 103167232UL,    2900736UL,    3494144UL, 4178063104UL, 3825806848UL, 3087739904UL, 
2181901824UL, 1326395392UL,  772944896UL,  303183104UL,    1259264UL,    1982976UL, 
3909106176UL, 3372233216UL, 2818584576UL, 2147495936UL, 1392521216UL,  855650816UL, 
 419443712UL,      13824UL,     866560UL, 3456122368UL, 2969581568UL, 2566927616UL, 
2080388096UL, 1543517440UL, 1073755648UL,  687880192UL,  352335872UL,      14080UL, 
3872000258UL, 3453223175UL, 2648440837UL, 1290141699UL,  351076352UL,   15534080UL, 
  15339776UL,   14169344UL,   13785600UL, 3904572160UL, 3754754051UL, 2832334848UL, 
1288699904UL,  348979200UL,   13175552UL,   12851712UL,   12399616UL,   12079104UL, 
3953003520UL, 3853125120UL, 2745171968UL, 1453786624UL,  581568768UL,   10881536UL, 
  11214080UL,   11089152UL,   10570240UL, 4067102464UL, 3798797824UL, 2825456896UL, 
1651314176UL,  829624320UL,  259723520UL,    8330240UL,    8729344UL,    8537344UL, 
4047377920UL, 3577419008UL, 2789151744UL, 1816335616UL, 1011291392UL,  458102272UL, 
   5183744UL,    6041600UL,    6308608UL, 4011989504UL, 3542227456UL, 2720208896UL, 
1898452992UL, 1160452096UL,  623843328UL,  120593408UL,    3680768UL,    4209152UL, 
4245624064UL, 3792771584UL, 3021019392UL, 2182355712UL, 1360403712UL,  823598848UL, 
 404232704UL,    1582080UL,    2240256UL, 4110425088UL, 3539998976UL, 2902464768UL, 
2181044736UL, 1375738624UL,  805313280UL,  436216064UL,       8448UL,     927744UL, 
3674220288UL, 3103794176UL, 2617254912UL, 2046829824UL, 1476404480UL, 1023419648UL, 
 654321408UL,  335554304UL,       9472UL, 3888645121UL, 3637772291UL, 3050897410UL, 
1977745408UL,  854196224UL,  233701376UL,   15400960UL,   15141632UL,   14494464UL, 
3904438272UL, 3653238784UL, 2864578560UL, 1774321664UL,  801570816UL,  214433792UL, 
  12977920UL,   12849664UL,   12658944UL, 3969646592UL, 3667853312UL, 2795241472UL, 
1721892864UL,  849870848UL,  229179392UL,   11142912UL,   11343104UL,   11282688UL, 
3983212544UL, 3664314368UL, 2808545280UL, 1684733952UL,  913440768UL,  309854208UL, 
   8390144UL,    9180672UL,    9251072UL, 3980331008UL, 3476751616UL, 2688155648UL, 
1715404800UL,  943915008UL,  491520000UL,    5373952UL,    6166016UL,    6760704UL, 
3794145024UL, 3324185600UL, 2619672832UL, 1831471360UL, 1127024896UL,  607127808UL, 
 204802304UL,    3871744UL,    4531200UL, 3944157696UL, 3440643840UL, 2736000256UL, 
1897270272UL, 1226312704UL,  739838976UL,  320604672UL,    2035968UL,    2694912UL, 
4161145600UL, 3607497728UL, 2936343552UL, 2164657152UL, 1443302912UL,  872877824UL, 
 503845120UL,  185273344UL,    1055488UL, 3976205056UL, 3305115904UL, 2701136384UL, 
2080379648UL, 1509954816UL,  989861120UL,  587207936UL,  318772992UL,       5888UL, 
3738435584UL, 3621060608UL, 3218210816UL, 2497183744UL, 1441071104UL,  720044032UL, 
 300810240UL,   15728640UL,   15728640UL, 3904307200UL, 3434151936UL, 2914320384UL, 
2176581632UL, 1287979008UL,  633995264UL,  248250368UL,   13500416UL,   13565952UL, 
3852009472UL, 3348234240UL, 2727608320UL, 1973157888UL, 1252327424UL,  631963648UL, 
 229507072UL,   11468800UL,   11730944UL, 3664314368UL, 3261333504UL, 2691235840UL, 
1852768256UL, 1215758336UL,  662568960UL,  226820096UL,    9175040UL,    9830400UL, 
3611230208UL, 3158245376UL, 2588082176UL, 1850212352UL, 1179516928UL,  710082560UL, 
 274202624UL,    6160384UL,    7208960UL, 3659857920UL, 3173384192UL, 2502492160UL, 
1798111232UL, 1160839168UL,  691208192UL,  322306048UL,    3932160UL,    4849664UL, 
3507486720UL, 3037790208UL, 2467561472UL, 1763115008UL, 1159331840UL,  706412544UL, 
 354287616UL,    2293760UL,    3080192UL, 3741581312UL, 3288662016UL, 2667970560UL, 
1896284160UL, 1225261056UL,  755564544UL,  436928512UL,  118423552UL,    1572864UL, 
4278190080UL, 3472883712UL, 2818572288UL, 2097152000UL, 1493172224UL, 1006632960UL, 
 620756992UL,  335544320UL,          0UL, 
 };

uint32_t ulMapBROADWAY_KCMY_3x3x2[ 9*9*9 ]=
{
1920105215UL,   60881733UL,   10551078UL,   10288922UL,   10223378UL,    9895694UL, 
   9895690UL,   10157829UL,   10157824UL, 4278246736UL,      65363UL,    8388394UL, 
   9895705UL,    9961232UL,    9895691UL,   10092296UL,   10092292UL,   10157824UL, 
4278966312UL, 2818631985UL,      65334UL,    6291229UL,    8257294UL,    9109254UL, 
  10223360UL,    9699072UL,    9633536UL, 4279751190UL, 3791969570UL, 2231430434UL, 
     65318UL,    4259603UL,    6553347UL,    7533568UL,    7859712UL,    8055296UL, 
4280339978UL, 4278246676UL, 3187729943UL, 1761669401UL,      65305UL,    2883338UL, 
   5041408UL,    6084608UL,    6608128UL, 4280732161UL, 4278246669UL, 3674398992UL, 
2717968655UL, 1459680272UL,      65295UL,    2095363UL,    4183808UL,    5098496UL, 
4279552258UL, 4279162627UL, 4043431433UL, 3271615752UL, 2315316489UL, 1191245065UL, 
  50396937UL,    1828864UL,    3525632UL, 4278830848UL, 4278767360UL, 4278245632UL, 
3707822336UL, 2936072195UL, 1996549891UL, 1006696195UL,      65283UL,    1759488UL, 
4278237952UL, 4278239744UL, 4110469632UL, 3674263296UL, 3254835200UL, 2516638720UL, 
1644223744UL,  822144768UL,      65280UL, 3706389867UL,   16138823UL,   64936234UL, 
  31323927UL,   46595346UL,   11992843UL,   11337480UL,   11337476UL,   11009792UL, 
4287273261UL, 2189593947UL,   10813229UL,   10747673UL,   10485519UL,   10354441UL, 
  10485509UL,   10551040UL,    9696256UL, 4283283480UL, 3641890107UL,  657252153UL, 
  57604636UL,    9109259UL,    9961219UL,   10026752UL,    9697280UL,    9039360UL, 
4282106121UL, 4278900765UL, 2517100065UL,  774168097UL,  172879376UL,    6747648UL, 
   7727616UL,    8054272UL,    8052992UL, 4281516545UL, 4279293453UL, 3355501844UL, 
1946870037UL,  858381071UL,  524541952UL,    5101568UL,    6082560UL,    6672640UL, 
4280532992UL, 4279293187UL, 3791773706UL, 2869551879UL, 1813699845UL,  858380291UL, 
 237622272UL,    3917568UL,    4964864UL, 4279354112UL, 4278767104UL, 4110473728UL, 
3238059010UL, 2383206400UL, 1477891328UL,  555275008UL,    1492992UL,    3324672UL, 
4278238464UL, 4127243776UL, 3774923264UL, 3288384512UL, 2634073344UL, 1828767744UL, 
1057475328UL,  235392768UL,    1556736UL, 4060131584UL, 3808472320UL, 3607147264UL, 
3288380928UL, 2835396864UL, 2248196352UL, 1543555072UL,  738249984UL,      53504UL, 
4293787704UL, 1291452479UL,   16138023UL,   15184662UL,   31578384UL,   81393413UL, 
  13827840UL,   12910336UL,   12451584UL, 4289880862UL, 2848079424UL,  350061354UL, 
  15058449UL,   31451141UL,   13826304UL,   12645632UL,   11464192UL,   10412032UL, 
4287139584UL, 4085422877UL, 2307494948UL,  949800976UL,  243856386UL,   11138816UL, 
  10219520UL,    9627136UL,    9099264UL, 4283998720UL, 4283741450UL, 3058153496UL, 
1515567640UL,  863227650UL,    7657728UL,    7984896UL,    8181248UL,    8114944UL, 
4281773568UL, 4281907968UL, 3677079305UL, 2284831499UL, 1380369157UL,  541837568UL, 
   5425152UL,    6342912UL,    6867712UL, 4280267008UL, 4279876608UL, 3960655874UL, 
2955134465UL, 1932051456UL,  976142592UL,  220970752UL,    3979520UL,    5159424UL, 
4278957056UL, 4278237696UL, 3909141504UL, 3104358144UL, 2248981760UL, 1393737472UL, 
 538294784UL,    1487616UL,    3124736UL, 4278235392UL, 3842025984UL, 3556814592UL, 
3103830272UL, 2449519104UL, 1744877056UL,  906016512UL,  184595968UL,    1420032UL, 
3858801664UL, 3573587456UL, 3372261376UL, 3053494784UL, 2550178816UL, 2046863616UL, 
1459663360UL,  687911936UL,      46080UL, 4293006619UL, 2918449187UL,  385744936UL, 
  16266776UL,   15374604UL,   15057667UL,   14802432UL,   13559552UL,   12314112UL, 
4290923277UL, 3957592103UL, 1138761255UL,   65824019UL,   15312642UL,   14534144UL, 
  13619968UL,   12637696UL,   11522816UL, 4288179200UL, 4205668878UL, 2611569687UL, 
1085699858UL,  281126656UL,   12303104UL,   11913216UL,   11258880UL,   10340864UL, 
4284640000UL, 4285956864UL, 3430714118UL, 2273809152UL, 1166453760UL,  158907392UL, 
   8504832UL,    8439808UL,    8242176UL, 4282089728UL, 4282552576UL, 3679493632UL, 
2690162944UL, 1633461760UL,  593078528UL,    5944320UL,    6732288UL,    7060992UL, 
4280325632UL, 4280196864UL, 3760366848UL, 2922292736UL, 1966187520UL, 1060480256UL, 
 221423360UL,    4368640UL,    5419008UL, 4278886144UL, 4278231296UL, 3640696832UL, 
3037701120UL, 2215879936UL, 1410704128UL,  555196416UL,    1612800UL,    3251456UL, 
4144013056UL, 3707802624UL, 3422590208UL, 3019938304UL, 2348850176UL, 1694539520UL, 
 889233152UL,  117479424UL,    1348608UL, 3724579328UL, 3489696256UL, 3238037760UL, 
2936048896UL, 2449510400UL, 1946194432UL, 1426102272UL,  671127808UL,      38400UL, 
4292615945UL, 3538944278UL, 1878523928UL,   16647962UL,   16330251UL,   15566339UL, 
  15249664UL,   14403072UL,   13421824UL, 4291180801UL, 4192668434UL, 2246838038UL, 
 300881686UL,   15948544UL,   14715392UL,   13937152UL,   13417472UL,   12435712UL, 
4288825344UL, 4290465028UL, 3149939976UL, 1539196173UL,  566847232UL,   12748032UL, 
  12625408UL,   12235776UL,   11384576UL, 4285617152UL, 4286734080UL, 3499386880UL, 
2459265792UL, 1251635200UL,    9927936UL,   10459904UL,   10332672UL,    9743872UL, 
4282666752UL, 4283392256UL, 3663424256UL, 2774692096UL, 1768518144UL,  677610240UL, 
   6394880UL,    7054848UL,    7318016UL, 4280575744UL, 4280643328UL, 3727324416UL, 
2872342272UL, 2034007040UL, 1128235264UL,  221938944UL,    4887040UL,    5742080UL, 
4279073024UL, 4278680832UL, 3658120448UL, 2953870080UL, 2216328960UL, 1461486080UL, 
 572294144UL,    1934592UL,    3508992UL, 4177559808UL, 3674241536UL, 3389028608UL, 
2969598464UL, 2332065024UL, 1644199424UL,  906002688UL,  100695040UL,    1343744UL, 
3623910656UL, 3389027840UL, 3187700736UL, 2868933888UL, 2399172864UL, 1895856384UL, 
1409318144UL,  721453312UL,      31488UL, 4292222976UL, 3807248909UL, 2700345356UL, 
1123745804UL,   16649227UL,   16458243UL,   15757824UL,   14785024UL,   14070272UL, 
4291175424UL, 4226027779UL, 2918383626UL, 1374620934UL,  149889537UL,   15090688UL, 
  14184960UL,   13537792UL,   13018880UL, 4289341696UL, 4290521088UL, 3418891777UL, 
2093493248UL,  818557952UL,   12993536UL,   12742912UL,   12553984UL,   12099840UL, 
4286263808UL, 4287051264UL, 3516152576UL, 2476228608UL, 1453212416UL,  279005696UL, 
  11037952UL,   11176704UL,   10721280UL, 4283579648UL, 4284171008UL, 3479586560UL, 
2708098048UL, 1836011264UL,  745689856UL,    7758592UL,    8617728UL,    8556032UL, 
4281153280UL, 4281287936UL, 3694545408UL, 2940162048UL, 2084918528UL, 1280070144UL, 
 272982784UL,    5076224UL,    5998080UL, 4279454720UL, 4279259648UL, 3725808896UL, 
2971096832UL, 2182895616UL, 1495424512UL,  572678912UL,    2319872UL,    3764992UL, 
4278214400UL, 3791674880UL, 3372244224UL, 2936036864UL, 2248170496UL, 1694983168UL, 
 956720384UL,  134242816UL,    1533952UL, 3590350336UL, 3321914112UL, 3070255360UL, 
2785042688UL, 2365612800UL, 1862296832UL, 1342203392UL,  704669696UL,      25856UL, 
4291827200UL, 4075356422UL, 3169976325UL, 1945632774UL,  687669253UL,   16583939UL, 
  16521216UL,   15293952UL,   14517248UL, 4291105792UL, 4292675840UL, 3371237376UL, 
2012151808UL,  518586368UL,   14882304UL,   14496000UL,   13786624UL,   13270528UL, 
4289664512UL, 4290514432UL, 3401449472UL, 2277968128UL, 1086852608UL,   12849920UL, 
  12990464UL,   12804096UL,   12418048UL, 4286978560UL, 4287764224UL, 3516273920UL, 
2509903872UL, 1537153536UL,  480517632UL,   11220480UL,   11492864UL,   11368960UL, 
4284163072UL, 4284490240UL, 3496419840UL, 2674729984UL, 1853040384UL,  947398912UL, 
   8007680UL,    9067008UL,    9532416UL, 4281739776UL, 4080544256UL, 3460114944UL, 
2756127744UL, 2051878400UL, 1330721024UL,  307443200UL,    6114816UL,    6907392UL, 
4280034048UL, 4279839488UL, 3625659648UL, 2988454144UL, 2200187648UL, 1512519168UL, 
 757936384UL,    2835968UL,    3889408UL, 4278596864UL, 4110431232UL, 3523228928UL, 
2969581056UL, 2214606592UL, 1644575744UL,  990659584UL,  168445440UL,    1592576UL, 
3741336832UL, 3389014784UL, 3070247936UL, 2684372480UL, 2298497024UL, 1828735232UL, 
1308642048UL,  654330624UL,      18688UL, 4291628544UL, 4142202880UL, 3521970176UL, 
2599682048UL, 1492779008UL,  519897088UL,   16647424UL,   16584704UL,   15289088UL, 
4291037184UL, 4292280320UL, 3470589952UL, 2547843072UL, 1457520640UL,  400424960UL, 
  14290176UL,   14098176UL,   13913088UL, 4290119424UL, 4290772992UL, 3418161152UL, 
2562785280UL, 1589903360UL,  465960960UL,   12979712UL,   13051136UL,   12865024UL, 
4287367168UL, 4287889408UL, 3466067968UL, 2593718272UL, 1738539008UL,  648085504UL, 
  11012608UL,   11610112UL,   11619840UL, 4284484864UL, 4200728320UL, 3462989312UL, 
2658206976UL, 1869940480UL, 1065027840UL,  159320576UL,    9054208UL,    9850624UL, 
4282193152UL, 4013691648UL, 3376549632UL, 2722828032UL, 2001735680UL, 1347621120UL, 
 441979392UL,    6366208UL,    7227392UL, 4280294400UL, 3961395456UL, 3374322944UL, 
2737181952UL, 2100040960UL, 1479611904UL,  724834048UL,    3612160UL,    4536832UL, 
4278915328UL, 4060550400UL, 3506902272UL, 2970228736UL, 2349537536UL, 1661868800UL, 
 974068992UL,  336860416UL,    1912576UL, 4076872192UL, 3456115200UL, 3087016704UL, 
2717918464UL, 2248157440UL, 1778395648UL, 1207970048UL,  587213824UL,      11264UL, 
4293459968UL, 4293787648UL, 3773825024UL, 3035824128UL, 2096562176UL, 1308229632UL, 
 587005952UL,  167641088UL,   16711680UL, 4291035136UL, 4022730752UL, 3469869056UL, 
2882797568UL, 2027487232UL, 1222443008UL,  501022720UL,   14483456UL,   14548992UL, 
4290314240UL, 3903848448UL, 3350659072UL, 2797404160UL, 2059468800UL, 1204027392UL, 
 449183744UL,   13041664UL,   13172736UL, 4153344000UL, 3733913600UL, 3348496384UL, 
2761687040UL, 2091122688UL, 1319567360UL,  480903168UL,   11468800UL,   11927552UL, 
4066770944UL, 3630759936UL, 3295608832UL, 2725773312UL, 2054881280UL, 1417740288UL, 
 562233344UL,    9109504UL,    9961472UL, 4282449920UL, 3762421760UL, 3242786816UL, 
2639265792UL, 2052587520UL, 1448804352UL,  710868992UL,    6488064UL,    7405568UL, 
3944218624UL, 3592290304UL, 3206742016UL, 2636906496UL, 2066808832UL, 1479868416UL, 
 792133632UL,  121372672UL,    5046272UL, 3976200192UL, 3590324224UL, 3238330368UL, 
2752118784UL, 2114846720UL, 1527906304UL,  924123136UL,  253296640UL,    2490368UL, 
4278190080UL, 3657433088UL, 3254779904UL, 2818572288UL, 2298478592UL, 1795162112UL, 
1224736768UL,  603979776UL,          0UL, 
};

APDK_END_NAMESPACE
