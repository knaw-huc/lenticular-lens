<template>
  <div>
    <p>
      The <strong>​Approximated ​Levenshtein Distance</strong> ​method is used to align ​<strong>​source</strong> a​nd
      <strong>​​target’s</strong> <strong>​I​nternationalized Resource Identifiers</strong> whenever the similarity
      score of their respective user selected property values are ​<strong>​above a given threshold​</strong>.
    </p>

    <p>
      <strong>Edit distance</strong> is a way of quantifying how ​<strong>dissimilar</strong> two strings (e.g., words)
      are to one another by counting the <strong>minimum number of operations</strong> ​<var>ε</var> ​
      (​removal, insertion, or substitution of a character in the string)​ required to transform one string
      into the other. For example, ​the ​Levenshtein distance between "kitten" and "sitting" is <var>​ε ​= 3</var>
      as it requires a two substitutions ("s" for "k" and "i" for "e") and one insertion of "g" at the end
      [<a href="https://en.wikipedia.org/wiki/Edit_distance">https://en.wikipedia.org/wiki/Edit_distance</a>]​.
    </p>

    <p>
      <strong>Normalisation ​Ω​:</strong> Because in this application, the <strong>​similarity score</strong>
      <var>​Ω</var> ​of a matching pair needs to be quantified in the interval ​<strong>[0, 1]</strong>​,
      the​ <strong>dissimilarity score</strong> <var>​ε</var> expressing the <strong>​minimum number of
      operations</strong> ​between two strings ​<strong>is then normalised</strong> as <var>​Ω</var>
      based on the length of the longest string. The <strong>​dissimilarity score​​</strong> <var>ε​ = 3</var> ​between
      ​"kitten" and "sitting" is then normalised to a <strong>​similarity score</strong> <var>Ω​ ​=​ ​1 - 3 / 7 =
      0.57​</var>.​
    </p>

    <p>
      <strong>Minimum threshold ​φ:</strong> Using this algorithm, ​a <strong>​minimum threshold value</strong>
      <var>φ​</var> <strong>​must</strong> be set in the interval ​<strong>[0,1]</strong>, ​such that finding any
      matched pairs of IRIs based on the similarity of their respective property values depends on whether or not
      the computed <var>​Ω</var> is ​<strong>equal or above</strong> <var>​φ</var>​. A threshold ​<var>φ = 1</var>
      equates an exact match. In our previous example, if a <strong>​minimum</strong> threshold of <var>​φ = ​0.7</var>
      is set, "kitten" and "sitting" will not be matched. ​<strong>In short</strong>, <var>​φ</var> is the user defined
      threshold when the similarity score ​<var>Ω</var> is selected for accepting or rejecting a match.
    </p>

    <p>
      <strong>Maximum character error threshold ​𝛿:</strong>​ In case the ​<strong>original edit distance
      score</strong> ​<var>ε</var> (minimum number of operations score) is preferred, the number of <strong>character
      errors</strong> <var>​𝛿</var> ​of choice is used instead as threshold for deciding whether a match is accepted or
      rejected. However, for consistency purposes, the corresponding normalisation value <var>​Ω</var> is still computed
      for the minimum number of operations score computed <var>​ε</var>​. For instance, in our previous example, if a
      <strong>​maximum ​characters errors</strong> i​s set to <var>​𝛿 = 3</var>, "kitten" and "sitting" will be matched
      but the computed strength will be <var>​Ω = ​0.57</var> a​nd ​not <var>​ε = 3</var> as is it only serves the
      purpose of decision maker. <strong>I​n short</strong>, <var>​𝛿</var> i​s the user defined threshold when the
      dissimilarity score <var>ε</var>​ ​is selected for accepting or rejecting a match.
    </p>

    <div>
      <p>Example:</p>

      <ol>
        <li>1. Levenshtein-distance (Rembrand van Rijn, Rembrandt Harmensz van Rijn) = 10</li>
        <li>2. Normalised-L​evenshtein-distance ​(Rembrand van Rijn, Rembrandt Harmensz van Rijn) = 0.63</li>
      </ol>

      <p>
        If <var>​φ = 0.7</var> t​hen <code>​[​Rembrand van Rijn] owl:sameAs [Rembrandt Harmensz van Rijn]</code>
        <strong>is rejected​</strong> because <var>Ω​ = 0.63 < φ​</var>.
      </p>

      <p>
        If <var>​δ = 5</var> t​hen <code>[​​Rembrand van Rijn] and [Rembrandt Harmensz van Rijn]</code>
        <strong>is ​rejected</strong> because <var>ε ​= 10 >​ ​δ</var>.
      </p>
    </div>
  </div>
</template>