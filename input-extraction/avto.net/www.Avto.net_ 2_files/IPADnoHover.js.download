$(function()
{
	if ('createTouch' in document)
	{
		try
		{
			var ignore = /:hover\b/;
			for (var i=0; i<document.styleSheets.length; i++)
			{
				var sheet = document.styleSheets[i];
				for (var j=sheet.cssRules.length-1; j>=0; j--)
				{
					var rule = sheet.cssRules[j];
					if (rule.type === CSSRule.STYLE_RULE && ignore.test(rule.selectorText))
					{
						sheet.deleteRule(j);
					}
				}
			}
		}
		catch(e){}
	}
});
