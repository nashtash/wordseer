/* Copyright 2012 Aditi Muralidharan. See the file "LICENSE" for the full license governing this code. */Ext.define('WordSeer.store.DocumentStore', {
	extend:'Ext.data.Store',
	model:'WordSeer.model.DocumentModel',
	proxy: {
		type:'ajax',
		noCache: false,
		reader: {
			type: 'json',
			root: 'results',
		},
		url: ws_api_path + 'documents/search-results/',
		extraParams: {
			instance:getInstance(),
	        user:getUsername(),
	        include_text: false,
	    },
	},
})
