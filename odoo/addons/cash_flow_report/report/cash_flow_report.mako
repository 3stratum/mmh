<!DOCTYPE html SYSTEM "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <style>
            ${css}
        </style>
    </head>
    <body>
        <%setLang(user.lang)%>
        <%
            fiscalyear = get_fiscal_year(data)    
        %>
         <div class="table header">
            <div class="table-row">
                <div class="table-cell logo">${helper.embed_logo_by_name('default_logo', height=40, width=150)|n}</div>
                <div class="table-cell text">
                    <p class="company">${fiscalyear.company_id.name}</p>
                    <p class="title">${_('Cash Flow Report')}</p>
                </div>
            </div>
        </div>
       <div class="table list">
            <div class="table-header">
                <div class="table-row labels no-wrap">
                    <div class="table-cell first-column" style="width: 70px">${_('Chart of Accounts: ')}<br/>${get_chart_account_id(data).name}</div>
                    <div class="table-cell" style="width: 70px">${_('Fiscal Year')}<br/>${get_fiscal_year(data).name}</div>
                    <div class="table-cell" style="width: 70px">
                        %if get_filter(data) == 'filter_date':
                            ${_('Dates Filter')}
                        %elif get_filter(data) == 'filter_period':
                            ${_('Periods Filter')}
                        %else:
                            ${_('No filters')}
                        %endif
                    <br/>
                    %if get_filter(data) != 'filter_no':
                        ${_('From:')}
                            %if get_filter(data) == 'filter_date':
                                ${formatLang(get_date_from(data), date=True)}
                            %else:
                                ${get_start_period(data).name}
                            %endif
                            ${_('To:')}
                            %if get_filter(data) == 'filter_date':
                                ${ formatLang(get_date_to(data), date=True)}
                            %else:
                                ${get_end_period(data).name}
                            %endif
                    %endif
                    </div>
                    <div class="table-cell last-column" style="width: 70px">${_('Target Moves')}<br/>${ display_target_move(data) }</div>
                </div>
            </div>          
        </div>
        
        <% cash_flow_amounts, cash_flow_types, total_by_type, enable_comparison, period_names,cash_at_begin_period,cash_at_end_period = get_data(cr, uid, data,context)%>
        
        %for type, cash_flow in cash_flow_types.iteritems():
           <br/>
           <div class="table header">
                <div class="table-row">
                   <div class="table-cell text">
                        %if type == 'operation':
                            <p class="subtitle">${_('Type') + ': ' + _('Operation') }</p>
                        %elif type == 'investment': 
                            <p class="subtitle">${_('Type') + ': ' + _('Investment') }</p>
                        %elif type == 'financing': 
                            <p class="subtitle">${_('Type') + ': ' + _('Financing') }</p>
                        %endif
                   </div>
                </div>
           </div>
           <div class="table list">
                <div class="table-header">
                    <div class="table-row labels no-wrap">
                        <div class="table-cell first-column">${_('Name')}</div>
                        %if enable_comparison:

                            %for i in period_names:
                                <div class="table-cell last-column">${(i)}</div>
                            %endfor
                        %else:
                           
                            <div class="table-cell">${_('Debit')}</div>
                            <div class="table-cell">${_('Credit')}</div>
                            <div class="table-cell">${_('Balance')}</div>
                        %endif

                            
                    </div>
                </div>
                <div class="table-body"> 
                    <% row_even = False %>
                    %for id in cash_flow:
                        <div class="table-row ${row_even and 'even' or 'odd'}">
                            %if id in cash_flow_amounts.keys():
                                <% cash_tuple = cash_flow_amounts[id] %>
                                <div class="table-cell first-column">${cash_tuple[1]}</div>
                                %if enable_comparison:
                                    %for i in range(2,len(cash_tuple)):
                                        <div class="table-cell amount">${(cash_tuple[i])}</div>
                                    %endfor

                                %else:
                                
                                    <div class="table-cell amount">${formatLang(cash_tuple[2])}</div>
                                    <div class="table-cell amount">${formatLang(cash_tuple[3])}</div>
                                    <div class="table-cell amount last-column">${formatLang(cash_tuple[4])}</div>
                                %endif
                            %endif
                        <%
                            if row_even:
                                row_even = False
                            else:
                                row_even = True
                        %>
                        </div>
                    %endfor
                </div>
                <br/>
                
                %if enable_comparison:
                    <div class="table-row subtotal">
                        %for subtotal in total_by_type[type]:
                            <div class="table-cell amount">${(subtotal)}</div>
                        %endfor
                    </div>
                %else:

                    <div class="table-row subtotal">
                        <div class="table-cell first-column"></div>
                        <div class="table-cell"></div>
                        <div class="table-cell amount">${_('Total')}</div>
                        <div class="table-cell amount last-column">${formatLang(total_by_type[type])}</div>
                    </div>
                %endif


           </div>
        %endfor

        %if cash_at_begin_period and cash_at_end_period:
            <div class="table header">
                <div class="table-row total">
                    <div class="table-cell first-column">${_('Begin Cash')}</div>
                    %for key,value in sorted(cash_at_begin_period.iteritems()):
                        <div class="table-cell amount last-column">${(cash_at_begin_period[key])}</div>
                    %endfor
                </div>
                <div class="table-row total">
                    <div class="table-cell first-column">${_('End Cash')}</div>
                    %for key,value in sorted(cash_at_end_period.iteritems()):
                        <div class="table-cell amount last-column">${(cash_at_end_period[key])}</div>
                    %endfor
                </div>
            </div>
        %endif
        <div class="table-row spacer">
            <div class="table-cell">&nbsp;</div>
        </div>
        <% 
           signatures = get_signatures_report(cr, uid, 'Cash Flow Report')
           cont = 0
        %>
        %if len(signatures) > 0:
            <div class="table header">
                <div class="table-row">
                    <div class="table-cell text">
                        <p class="title">${_('Authorized by: ')}</p>
                    </div>
                </div>
           </div>
           <br/><br/>
           <div class="table header">
                <div class="table-row">
                    <div class="table-cell text">
                    %for user_sign in signatures:
                        <div class="table-cell text">_________________________________________________________<br/>
                                                        <p class="subtitle">${user_sign.name}</p>
                                                        <p class="company"><i>${user_sign.job_id.name or ''}</i></p>
                        </div>
                        <br/><br/><br/>
                    </div>
                    %endfor                
                </div>
            </div>
        %endif
        <p style="page-break-after:always"></p>
    </body>
</html>
