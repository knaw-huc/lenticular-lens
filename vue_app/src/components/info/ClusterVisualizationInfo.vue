<template>
  <button-info popup_title="CLUSTER VISUALIZATION">
    <div class="text-left">
      <div class="h2">Identity Link Network (ILN)</div>

      <p class="h5 pt-4 pl-5">
        This provides additional information of Identity Link Clusters:
      </p>

      <ul class="h5 ml-5">
        <li>Identity Link Clusters.</li>
        <li>Visualize a cluster and interact with it.</li>
        <li>An improved visualisation (particularly important for large clusters).</li>
        <li>Reconcile a cluster using additional information such relation.</li>
      </ul>

      <div class="h3 pt-4">An ILN of <strong>Meulder Hans</strong> in the Turtle Language</div>
      <p class="h5 pt-4 pb-4 pl-5">
        This is an example of links discovered using an approximate string similarity on
        <strong>Ecartico</strong>, <strong>Baptism</strong>, <strong>Marriage</strong> and
        <strong>Burial</strong> for married Amsterdammers between 1600 and 1650. These links are
        specifically the ones that link different occurrences of <strong>Meulder Hans</strong>.
      </p>

      <textarea disabled cols="75" rows="18" class="ml-5 mb-1">
        @prefix baptism: <http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/> .
        @prefix ecartico: <http://www.vondel.humanities.uva.nl/ecartico/persons/> .
        @prefix marriage: <http://goldenagents.org/uva/SAA/person/IndexOpOndertrouwregister/> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .

        baptism:saaId24678323p2 owl:sameAs ecartico:15747 .
        baptism:saaId24678323p2 owl:sameAs marriage:saaId26379331p1 .
        baptism:saaId24519437p2 owl:sameAs marriage:saaId26379331p1 .
        baptism:saaId24285260p2 owl:sameAs baptism:saaId24519437p2 .
        marriage:saaId26379331p1 owl:sameAs ecartico:15747 .
        baptism:saaId24519437p2 owl:sameAs ecartico:15747 .
        baptism:saaId24519437p2 owl:sameAs marriage:saaId26377774p1 .
        baptism:saaId24285260p2 owl:sameAs ecartico:15747 .
        baptism:saaId24285260p2 owl:sameAs marriage:saaId26379331p1 .
        baptism:saaId24519437p2 owl:sameAs baptism:saaId24678323p2 .
        marriage:saaId26377774p1 owl:sameAs ecartico:15747 .
        marriage:saaId26377774p1 owl:sameAs marriage:saaId26379331p1 .
        baptism:saaId24285260p2 owl:sameAs baptism:saaId24678323p2 .
      </textarea>

      <div class="h3 pt-4">Visualizing an ILN of <strong>Meulder Hans</strong></div>

      <p class="h5 pt-4 pl-5">
        The cluster of <strong>Meulder Hans</strong> is composed of 6 nodes (potentially the same person)
        using 13 link. The links in plain black represent an exact match (link strength = 1) while those in
        dotted red represent a link of strength below 1. The color of the node depicts the data-source it is
        stemmed from. So in this real example cluster,
      </p>

      <ul class="h5 ml-5">
        <li>Three nodes are from <strong>Baptism</strong>;</li>
        <li>Two nodes are from <strong>Marriage</strong> and;</li>
        <li>One is from <strong>Ecartico</strong>.</li>
      </ul>

      <div class="text-center pt-4">
        <img src="/static/images/1 Meulder Hans (Cluster).jpg" width="700" height="600"/>
      </div>
    </div>
  </button-info>
</template>