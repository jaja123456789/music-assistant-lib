(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["playerqueue"],{b097:function(e,t,i){"use strict";i.r(t);var s=function(){var e=this,t=e.$createElement,i=e._self._c||t;return i("section",[i("v-tabs",{model:{value:e.activeTab,callback:function(t){e.activeTab=t},expression:"activeTab"}},[i("v-tab",[e._v(" "+e._s(e.$t("queue_next_tracks")+" ("+e.next_items.length+")"))]),i("v-tab-item",[i("v-list",{attrs:{"two-line":""}},[i("RecycleScroller",{staticClass:"scroller",attrs:{items:e.next_items,"item-size":72,"key-field":"queue_item_id","page-mode":""},scopedSlots:e._u([{key:"default",fn:function(t){var s=t.item;return[i("ListviewItem",{attrs:{item:s,hideavatar:3==s.media_type&&e.$store.isMobile,hidetracknum:!0,hideproviders:e.$store.isMobile,hidelibrary:e.$store.isMobile,hidemenu:e.$store.isMobile},on:{click:e.itemClicked,menuClick:e.menuClick}})]}}])})],1)],1),i("v-tab",[e._v(" "+e._s(e.$t("queue_previous_tracks")+" ("+e.previous_items.length+")"))]),i("v-tab-item",[i("v-list",{attrs:{"two-line":""}},[i("RecycleScroller",{staticClass:"scroller",attrs:{items:e.previous_items,"item-size":72,"key-field":"queue_item_id","page-mode":""},scopedSlots:e._u([{key:"default",fn:function(t){var s=t.item;return[i("ListviewItem",{attrs:{item:s,hideavatar:3==s.media_type&&e.$store.isMobile,hidetracknum:!0,hideproviders:e.$store.isMobile,hidelibrary:e.$store.isMobile,hidemenu:e.$store.isMobile},on:{click:e.itemClicked,menuClick:e.menuClick}})]}}])})],1)],1)],1)],1)},r=[],a=(i("a4d3"),i("e01a"),i("d28b"),i("fb6a"),i("d3b7"),i("3ca3"),i("ddb0"),i("96cf"),i("89ba")),n=i("2b0e"),u=i("d3cc"),c={components:{ListviewItem:u["a"]},props:{},data:function(){return{selected:[2],items:[]}},computed:{next_items:function(){return this.items&&this.$server.activePlayer?this.items.slice(this.$server.activePlayer.cur_queue_index):[]},previous_items:function(){return this.items&&this.$server.activePlayer?this.items.slice(0,this.$server.activePlayer.cur_queue_index):[]}},created:function(){this.$store.windowtitle=this.$t("queue"),this.$server.activePlayer&&this.getItems(),this.$server.$on("queue updated",this.queueUpdatedMsg),this.$server.$on("new player selected",this.queueUpdatedMsg)},beforeDestroy:function(){this.$server.$off("queue updated"),this.$server.$off("new player selected")},methods:{itemClicked:function(e){var t="";if(1===e.media_type)t="/artists/"+e.item_id;else if(2===e.media_type)t="/albums/"+e.item_id;else{if(4!==e.media_type)return void this.$server.$emit("showContextMenu",e);t="/playlists/"+e.item_id}this.$router.push({path:t,query:{provider:e.provider}})},menuClick:function(e){this.$server.$emit("showContextMenu",e)},queueUpdatedMsg:function(e){e===this.$server.activePlayerId&&this.getItems()},getItems:function(){var e=Object(a["a"])(regeneratorRuntime.mark((function e(){var t,i,s,r,a,u,c,o,l,d,m;return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:t=0,i=50,s=0,r="players/"+this.$server.activePlayerId+"/queue";case 4:return e.next=7,this.$server.getData(r,{offset:t,limit:i});case 7:if(a=e.sent,a&&0!==a.length){e.next=10;break}return e.abrupt("break",34);case 10:for(u=!0,c=!1,o=void 0,e.prev=13,l=a[Symbol.iterator]();!(u=(d=l.next()).done);u=!0)m=d.value,this.items.length>=s?n["a"].set(this.items,s,m):this.items.push(m),s+=1;e.next=21;break;case 17:e.prev=17,e.t0=e["catch"](13),c=!0,o=e.t0;case 21:e.prev=21,e.prev=22,u||null==l.return||l.return();case 24:if(e.prev=24,!c){e.next=27;break}throw o;case 27:return e.finish(24);case 28:return e.finish(21);case 29:if(t+=i,!(a.length<i)){e.next=32;break}return e.abrupt("break",34);case 32:e.next=4;break;case 34:this.items.length>s&&(this.items=this.items.slice(0,s+1));case 35:case"end":return e.stop()}}),e,this,[[13,17,21,29],[22,,24,28]])})));function t(){return e.apply(this,arguments)}return t}()}},o=c,l=i("2877"),d=i("6544"),m=i.n(d),h=i("8860"),v=i("71a3"),p=i("c671"),b=i("fe57"),f=Object(l["a"])(o,s,r,!1,null,null,null);t["default"]=f.exports;m()(f,{VList:h["a"],VTab:v["a"],VTabItem:p["a"],VTabs:b["a"]})}}]);
//# sourceMappingURL=playerqueue.5fa460a7.js.map